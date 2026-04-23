"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Shield, AlertTriangle, Activity, Terminal,
  Lock, Globe, Cpu, Radio, Zap, LogOut,
} from "lucide-react";
import { useAuth } from "@clerk/nextjs";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const WS_BASE =
  process.env.NEXT_PUBLIC_WS_URL ||
  (typeof window !== "undefined"
    ? API_BASE.replace(/^http/, "ws")
    : "ws://localhost:8000");

// ─────────────────────────────────────────────────────────────
// Authenticated fetch helper
// ─────────────────────────────────────────────────────────────
async function apiFetch(url: string, token: string) {
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 401) throw new Error("401");
  return res.json();
}

// ─────────────────────────────────────────────────────────────
// Root — Clerk Auth gate
// ─────────────────────────────────────────────────────────────
export default function Root() {
  const { isSignedIn, getToken, signOut } = useAuth();
  const [backendToken, setBackendToken] = useState<string | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);

  // Restore cached backend token or exchange a fresh Clerk token
  useEffect(() => {
    if (!isSignedIn) {
      setBackendToken(null);
      return;
    }

    const cached = localStorage.getItem("aegis_token");
    if (cached) {
      setBackendToken(cached);
      return;
    }

    // Exchange Clerk session token → backend JWT
    (async () => {
      try {
        const clerkToken = await getToken();
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 10_000);

        const res = await fetch(`${API_BASE}/api/v1/auth/clerk`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${clerkToken}`,
          },
          signal: controller.signal,
        });
        clearTimeout(timeout);

        if (!res.ok) throw new Error(`Backend auth failed: ${res.status}`);
        const data = await res.json();
        localStorage.setItem("aegis_token", data.access_token);
        setBackendToken(data.access_token);
      } catch (err: unknown) {
        setAuthError(
          err instanceof Error ? err.message : "Backend connection failed"
        );
      }
    })();
  }, [isSignedIn, getToken]);

  const handleLogout = () => {
    localStorage.removeItem("aegis_token");
    setBackendToken(null);
    signOut();
  };

  // Not signed in → middleware redirects, but show nothing here
  if (!isSignedIn) return null;

  if (authError)
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-red-400 bg-red-950/40 border border-red-500/30 rounded-xl p-8 max-w-md text-center font-mono">
          <p className="text-lg font-bold mb-2">⚠ Backend Unreachable</p>
          <p className="text-sm text-red-300">{authError}</p>
          <p className="text-xs text-slate-500 mt-4">
            Ensure the backend is running on {API_BASE}
          </p>
        </div>
      </div>
    );

  if (!backendToken)
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-cyan-400 font-mono text-sm flex items-center gap-3">
          <span className="w-4 h-4 border-2 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin" />
          ESTABLISHING SECURE CHANNEL…
        </div>
      </div>
    );

  return <Dashboard token={backendToken} onLogout={handleLogout} />;
}

// ─────────────────────────────────────────────────────────────
// Dashboard
// ─────────────────────────────────────────────────────────────
function Dashboard({ token, onLogout }: { token: string; onLogout: () => void }) {
  const [activeTab, setActiveTab] = useState("overview");
  const [stats, setStats] = useState<any>(null);
  const [incidents, setIncidents] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);
  const [currentTime, setCurrentTime] = useState<string>("");
  const [wsStatus, setWsStatus] = useState<"connecting" | "open" | "closed">("closed");
  const wsRef = useRef<WebSocket | null>(null);

  // ── Clock ──
  useEffect(() => {
    const t = setInterval(
      () => setCurrentTime(new Date().toLocaleTimeString("en-US", { hour12: false })),
      1000
    );
    return () => clearInterval(t);
  }, []);

  // ── REST helpers ──
  const fetchStats = useCallback(async () => {
    try {
      const data = await apiFetch(`${API_BASE}/api/v1/dashboard/stats`, token);
      setStats(data);
    } catch (e: any) {
      if (e.message === "401") onLogout();
    }
  }, [token, onLogout]);

  const fetchIncidents = useCallback(async () => {
    try {
      const data = await apiFetch(`${API_BASE}/api/v1/dashboard/incidents`, token);
      setIncidents(data);
    } catch { /* silent */ }
  }, [token]);

  const fetchAlerts = useCallback(async () => {
    try {
      const data = await apiFetch(`${API_BASE}/api/v1/dashboard/alerts`, token);
      setAlerts(data);
    } catch { /* silent */ }
  }, [token]);

  const fetchLogs = useCallback(async () => {
    try {
      const data = await apiFetch(`${API_BASE}/api/v1/dashboard/logs`, token);
      setLogs(data);
    } catch { /* silent */ }
  }, [token]);

  // ── Initial REST load ──
  useEffect(() => {
    fetchStats();
    fetchIncidents();
    fetchAlerts();
    fetchLogs();
  }, [fetchStats, fetchIncidents, fetchAlerts, fetchLogs]);

  // ── WebSocket live feed (replaces setInterval) ──
  useEffect(() => {
    const wsUrl = `${WS_BASE}/api/v1/ws/feed?token=${token}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    setWsStatus("connecting");

    ws.onopen = () => setWsStatus("open");
    ws.onclose = () => setWsStatus("closed");
    ws.onerror = () => setWsStatus("closed");

    ws.onmessage = (event) => {
      try {
        const logEntry = JSON.parse(event.data);

        // Prepend to logs (live stream) — keep last 200
        setLogs((prev) => [logEntry, ...prev].slice(0, 200));

        // If it has alerts, prepend to alerts feed
        if (logEntry.alerts?.length) {
          const newAlerts = logEntry.alerts.map((a: string) => ({
            timestamp: logEntry.timestamp,
            source_ip: logEntry.ip,
            rule_name: a,
            severity: logEntry.severity || "MEDIUM",
          }));
          setAlerts((prev) => [...newAlerts, ...prev].slice(0, 100));
        }

        // If it has incidents, prepend to incidents
        if (logEntry.incidents?.length) {
          const newInc = logEntry.incidents.map((inc: string) => ({
            timestamp: logEntry.timestamp,
            incident: inc,
            severity: "CRITICAL",
          }));
          setIncidents((prev) => [...newInc, ...prev].slice(0, 50));
          // Bump the stats counter immediately
          setStats((s: any) =>
            s ? { ...s, total_incidents: (s.total_incidents || 0) + newInc.length } : s
          );
        }

        // Increment log counter in stats
        setStats((s: any) =>
          s ? { ...s, total_logs: (s.total_logs || 0) + 1 } : s
        );
      } catch { /* bad JSON */ }
    };

    // Fallback polling for stats every 30 s (WS doesn't carry aggregate stats)
    const pollStats = setInterval(fetchStats, 30_000);

    return () => {
      ws.close();
      clearInterval(pollStats);
    };
  }, [token, fetchStats]);

  return (
    <div className="min-h-screen p-4 md:p-8 relative z-10">
      <div className="scanline fixed inset-0 pointer-events-none z-50 opacity-10" />

      {/* Header */}
      <header className="mb-10 flex flex-col md:flex-row justify-between items-end border-b border-cyan-900/50 pb-4">
        <motion.div
          initial={{ x: -50, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          className="flex items-center gap-6"
        >
          <div className="relative">
            <Shield className="w-16 h-16 text-cyan-400 drop-shadow-[0_0_10px_rgba(34,211,238,0.5)]" />
            <div className="absolute top-0 right-0 w-3 h-3 bg-red-500 rounded-full animate-ping" />
          </div>
          <div>
            <h1 className="text-4xl md:text-5xl font-black tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 drop-shadow-lg">
              AEGIS<span className="text-xs align-top ml-2 opacity-50">v2.0</span>
            </h1>
            <div className="text-xs text-cyan-700 tracking-[0.5em] flex items-center gap-2">
              <span className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse" />
              INTELLIGENT THREAT DEFENSE
            </div>
          </div>
        </motion.div>

        <div className="flex items-center gap-6 mt-4 md:mt-0 font-mono text-sm">
          {/* WS status */}
          <div className="text-right">
            <div className="text-xs text-slate-500 uppercase">Feed</div>
            <div
              className={`text-xs font-bold flex items-center gap-1 ${
                wsStatus === "open"
                  ? "text-emerald-400"
                  : wsStatus === "connecting"
                  ? "text-yellow-400"
                  : "text-red-400"
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full ${
                  wsStatus === "open"
                    ? "bg-emerald-400 animate-pulse"
                    : wsStatus === "connecting"
                    ? "bg-yellow-400 animate-ping"
                    : "bg-red-400"
                }`}
              />
              {wsStatus === "open" ? "WS LIVE" : wsStatus === "connecting" ? "CONNECTING" : "POLLING"}
            </div>
          </div>

          <div className="h-10 w-[1px] bg-cyan-900/50" />

          <div className="text-right">
            <div className="text-xs text-slate-500 uppercase">System Time</div>
            <div className="text-xl text-cyan-400 font-bold">{currentTime}</div>
          </div>

          <div className="h-10 w-[1px] bg-cyan-900/50" />

          <div className="text-right">
            <div className="text-xs text-slate-500 uppercase">Status</div>
            <div className="text-green-400 font-bold flex items-center gap-2">
              <Activity className="w-4 h-4" /> ONLINE
            </div>
          </div>

          {/* Logout */}
          <button
            id="aegis-logout-btn"
            onClick={onLogout}
            title="Sign out"
            className="ml-2 text-slate-600 hover:text-red-400 transition-colors"
          >
            <LogOut className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Navigation */}
      <nav className="flex gap-6 mb-10 overflow-x-auto pb-2">
        {["overview", "alerts", "logs"].map((tab) => (
          <button
            key={tab}
            id={`tab-${tab}`}
            onClick={() => setActiveTab(tab)}
            className={`relative px-8 py-3 rounded-sm font-bold tracking-widest uppercase text-sm transition-all duration-300 ${
              activeTab === tab
                ? "bg-cyan-950/40 text-cyan-300 border-b-2 border-cyan-400 shadow-[0_0_20px_rgba(34,211,238,0.2)]"
                : "text-slate-600 hover:text-cyan-600 hover:bg-slate-900/50"
            }`}
          >
            {tab}
            {activeTab === tab && (
              <motion.div
                layoutId="activeTab"
                className="absolute inset-0 bg-gradient-to-t from-cyan-500/10 to-transparent pointer-events-none"
              />
            )}
          </button>
        ))}
      </nav>

      {/* Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          transition={{ duration: 0.2 }}
        >
          {activeTab === "overview" && <OverviewTab stats={stats} incidents={incidents} />}
          {activeTab === "alerts" && <AlertsTab alerts={alerts} />}
          {activeTab === "logs" && <LogsTab logs={logs} />}
        </motion.div>
      </AnimatePresence>

      <footer className="fixed bottom-0 left-0 w-full p-2 bg-slate-950/80 backdrop-blur text-center text-[10px] text-slate-600 font-mono border-t border-slate-900 z-40">
        AEGIS SECURE SYSTEM // UNQUAM DORMIAMUS // ENCRYPTED CONNECTION ESTABLISHED // SECURED BY <a href="https://www.linkedin.com/in/aditya-singh-83a5b81bb/" target="_blank" rel="noopener noreferrer" className="hover:text-cyan-400 transition-colors underline decoration-cyan-900/50 underline-offset-4">ADITYA SINGH</a>
      </footer>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Tab components
// ─────────────────────────────────────────────────────────────────────────────

function OverviewTab({ stats, incidents }: { stats: any; incidents: any[] }) {
  return (
    <div className="space-y-8">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
        <StatCard label="Total Logs"       value={stats?.total_logs ?? 0}                                        icon={<Cpu className="w-6 h-6" />}      color="cyan"    delay={0}   />
        <StatCard label="Ingestion (EPS)"  value={stats?.eps ? `${stats.eps.toLocaleString()}+` : "0"}           icon={<Zap className="w-6 h-6" />}      color="emerald" delay={0.1} />
        <StatCard label="Response Time"    value={stats?.avg_response_ms ? `<${stats.avg_response_ms}ms` : "0ms"} icon={<Activity className="w-6 h-6" />} color="blue"    delay={0.2} />
        <StatCard label="Threat Alerts"    value={stats?.total_alerts ?? 0}                                       icon={<Radio className="w-6 h-6" />}    color="yellow"  delay={0.3} />
        <StatCard label="Active Incidents" value={stats?.total_incidents ?? 0}                                    icon={<Shield className="w-6 h-6" />}   color="red"     delay={0.4} pulse />
        <StatCard label="Critical 24 h"   value={stats?.critical_last_24h ?? 0}                                  icon={<Lock className="w-6 h-6" />}     color="purple"  delay={0.5} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass-panel p-6 rounded-lg relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-1 h-full bg-cyan-500/50" />
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-xl text-cyan-300 flex items-center gap-2">
              <Globe className="w-5 h-5 animate-pulse" /> GLOBAL INCIDENT TRACKER
            </h3>
            <span className="text-xs text-cyan-800 border border-cyan-900 px-2 py-1 rounded">
              LIVE FEED
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="text-xs text-slate-500 border-b border-slate-800 uppercase tracking-widest">
                  <th className="p-3">Time</th>
                  <th className="p-3">Threat Detection</th>
                  <th className="p-3">Level</th>
                  <th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody className="font-mono text-sm">
                {incidents.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="p-8 text-center text-slate-700 italic">
                      -- NO ACTIVE THREATS DETECTED --
                    </td>
                  </tr>
                ) : (
                  incidents.map((inc, i) => (
                    <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/20 transition-colors">
                      <td className="p-3 text-slate-400">
                        {new Date(inc.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="p-3 text-slate-200">
                        <span className="text-cyan-400 font-bold mr-2">➜</span>
                        {inc.incident}
                      </td>
                      <td className="p-3"><SeverityBadge severity="CRITICAL" /></td>
                      <td className="p-3 text-xs">
                        <span className="bg-red-500/10 text-red-500 px-2 py-1 rounded border border-red-500/20 animate-pulse">
                          ACTIVE
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="glass-panel p-6 rounded-lg flex flex-col items-center justify-center text-center relative overflow-hidden">
          <Shield className="w-24 h-24 text-slate-800 mb-4" />
          <h4 className="text-slate-500 font-bold mb-2">SYSTEM INTEGRITY</h4>
          <div className="text-5xl font-black text-emerald-500 drop-shadow-[0_0_15px_rgba(16,185,129,0.5)]">
            98%
          </div>
          <div className="w-full h-2 bg-slate-800 rounded-full mt-4 overflow-hidden">
            <div className="h-full bg-emerald-500 w-[98%] shadow-[0_0_10px_rgba(16,185,129,1)]" />
          </div>
        </div>
      </div>
    </div>
  );
}

function AlertsTab({ alerts }: { alerts: any[] }) {
  return (
    <div className="glass-panel p-6 rounded-lg min-h-[600px]">
      <h3 className="text-xl text-yellow-400 mb-6 flex items-center gap-3">
        <AlertTriangle className="w-6 h-6" /> SECURITY ALERTS
        <span className="ml-auto text-xs text-slate-600 font-mono">{alerts.length} events</span>
      </h3>
      <div className="grid gap-3">
        {alerts.length === 0 && (
          <div className="text-slate-700 text-center py-12 italic">-- No alerts yet --</div>
        )}
        {alerts.map((alert, i) => (
          <motion.div
            key={i}
            initial={{ x: -20, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: Math.min(i * 0.04, 0.5) }}
            className="bg-slate-900/80 border-l-4 border-yellow-500 p-4 flex justify-between items-center group hover:bg-slate-800 transition-all"
          >
            <div>
              <div className="text-sm text-slate-400 font-mono mb-1 flex items-center gap-2">
                <span>{typeof alert.timestamp === "string" ? alert.timestamp.replace("T", " ").slice(0, 19) : alert.timestamp}</span>
                <span className="text-slate-700">|</span>
                <span className="text-cyan-600">{alert.source_ip || "—"}</span>
              </div>
              <div className="text-lg font-bold text-slate-200 group-hover:text-yellow-400 transition-colors">
                {alert.rule_name}
              </div>
            </div>
            <SeverityBadge severity={alert.severity} />
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function LogsTab({ logs }: { logs: any[] }) {
  return (
    <div className="glass-panel p-1 rounded-lg border-2 border-slate-800 bg-black min-h-[600px] font-mono text-xs md:text-sm overflow-hidden flex flex-col">
      <div className="bg-slate-900 p-2 flex items-center justify-between border-b border-slate-800 text-slate-500 text-xs uppercase tracking-wider">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4" /> Live Log Stream
          <span className="text-slate-700">({logs.length})</span>
        </div>
        <div className="flex gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50" />
          <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50" />
          <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50" />
        </div>
      </div>
      <div className="p-4 space-y-1 overflow-y-auto max-h-[700px]">
        {logs.map((log, i) => (
          <div key={i} className="flex gap-4 border-b border-slate-900/50 pb-1 mb-1 hover:bg-white/5 transition-colors">
            <span className="text-slate-600 shrink-0 select-none w-36">
              {typeof log.timestamp === "string" ? log.timestamp.replace("T", " ").slice(0, 19) : log.timestamp}
            </span>
            <span className={`break-all ${log.level === "ERROR" ? "text-red-400" : "text-slate-300"}`}>
              <span className="text-cyan-700 mr-2">[{log.level || "INFO"}]</span>
              {log.message}
              {log.ml_anomaly && (
                <span className="ml-2 bg-purple-900/30 text-purple-400 px-1 border border-purple-500/30 text-[10px] uppercase">
                  Anomaly: {log.anomaly_explanation}
                </span>
              )}
            </span>
          </div>
        ))}
        {logs.length === 0 && (
          <div className="text-slate-700 animate-pulse">_ Waiting for data stream…</div>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────
// UI helpers
// ─────────────────────────────────────────────────────────────

function StatCard({ label, value, icon, color, pulse, delay }: any) {
  const colors: any = {
    cyan:    "text-cyan-400 border-cyan-500/30 shadow-cyan-500/20",
    emerald: "text-emerald-400 border-emerald-500/30 shadow-emerald-500/20",
    blue:    "text-blue-400 border-blue-500/30 shadow-blue-500/20",
    yellow:  "text-yellow-400 border-yellow-500/30 shadow-yellow-500/20",
    red:     "text-red-400 border-red-500/30 shadow-red-500/20",
    purple:  "text-purple-400 border-purple-500/30 shadow-purple-500/20",
  };
  const theme = colors[color] || colors.cyan;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay }}
      className={`relative p-6 rounded-xl border bg-slate-900/60 backdrop-blur-sm overflow-hidden group ${theme} hover:border-opacity-100 transition-all duration-500`}
    >
      <div className="absolute top-0 right-0 p-4 opacity-20 group-hover:opacity-100 transition-opacity duration-500 transform group-hover:scale-110">
        {icon}
      </div>
      <div className="relative z-10">
        <h4 className="text-slate-500 text-xs uppercase tracking-widest font-bold mb-1">{label}</h4>
        <div className={`text-4xl font-black ${color === "red" ? "text-red-500" : "text-slate-100"} drop-shadow-lg flex items-center gap-2`}>
          {value}
          {pulse && (
            <span className="flex h-3 w-3 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500" />
            </span>
          )}
        </div>
      </div>
      <div className="absolute bottom-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-current to-transparent opacity-20" />
    </motion.div>
  );
}

function SeverityBadge({ severity }: { severity: string }) {
  const styles: any = {
    CRITICAL: "bg-red-950 text-red-500 border-red-600 animate-pulse",
    HIGH:     "bg-orange-950 text-orange-500 border-orange-600",
    MEDIUM:   "bg-yellow-950 text-yellow-500 border-yellow-600",
    LOW:      "bg-blue-950 text-blue-500 border-blue-600",
  };
  return (
    <span className={`px-3 py-1 rounded text-xs font-bold border ${styles[severity] || styles.LOW} uppercase tracking-wider shadow-[0_0_10px_rgba(0,0,0,0.5)]`}>
      {severity}
    </span>
  );
}
