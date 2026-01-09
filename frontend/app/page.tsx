"use client";

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Shield, AlertTriangle, Activity, Terminal, Lock, Globe } from 'lucide-react';

const API_BASE = "http://localhost:8000/api/v1/dashboard";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [stats, setStats] = useState<any>(null);
  const [incidents, setIncidents] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);

  useEffect(() => {
    fetchStats();
    fetchIncidents();
    const interval = setInterval(() => {
      fetchStats();
      // Poll based on active tab
      if (activeTab === 'alerts') fetchAlerts();
      if (activeTab === 'logs') fetchLogs();
    }, 5000);
    return () => clearInterval(interval);
  }, [activeTab]);

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/stats`);
      setStats(await res.json());
    } catch (e) { }
  };

  const fetchIncidents = async () => {
    try {
      const res = await fetch(`${API_BASE}/incidents`);
      setIncidents(await res.json());
    } catch (e) { }
  };

  const fetchAlerts = async () => {
    try {
      const res = await fetch(`${API_BASE}/alerts`);
      setAlerts(await res.json());
    } catch (e) { }
  };

  const fetchLogs = async () => {
    try {
      const res = await fetch(`${API_BASE}/logs`);
      setLogs(await res.json());
    } catch (e) { }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-8 font-mono">
      {/* Header */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="flex justify-between items-center mb-8 border-b border-cyan-900 pb-4"
      >
        <div className="flex items-center gap-4">
          <Shield className="w-10 h-10 text-cyan-400" />
          <div>
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 to-blue-600">
              AEGIS SIEM
            </h1>
            <p className="text-xs text-slate-500 tracking-widest">THREAT DETECTION & RESPONSE PLATFORM</p>
          </div>
        </div>
        <div className="flex gap-4 items-center">
          <span className="flex items-center gap-2 text-xs text-green-400 bg-green-900/20 px-3 py-1 rounded-full border border-green-900">
            <Activity className="w-3 h-3" /> SYSTEM ONLINE
          </span>
        </div>
      </motion.div>

      {/* Tabs */}
      <div className="flex gap-4 mb-8">
        {['overview', 'alerts', 'logs'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-6 py-2 rounded-lg border uppercase text-sm tracking-widest transition-all ${activeTab === tab
                ? 'border-cyan-500 bg-cyan-900/40 text-cyan-300 shadow-[0_0_15px_rgba(34,211,238,0.3)]'
                : 'border-slate-800 bg-slate-900/50 text-slate-500 hover:border-slate-700'
              }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard icon={<Shield />} label="Total Logs" value={stats?.total_logs || 0} color="text-blue-400" />
          <StatCard icon={<AlertTriangle />} label="Total Alerts" value={stats?.total_alerts || 0} color="text-yellow-400" />
          <StatCard icon={<Lock />} label="Active Incidents" value={stats?.total_incidents || 0} color="text-red-400" isFlash={stats?.total_incidents > 0} />
          <StatCard icon={<Globe />} label="Critical (24h)" value={stats?.critical_last_24h || 0} color="text-purple-400" />

          {/* Recent Incidents Table */}
          <div className="col-span-1 md:col-span-2 lg:col-span-4 bg-slate-900/50 border border-slate-800 rounded-xl p-6">
            <h3 className="text-xl font-bold mb-4 text-cyan-400">Recent Incidents</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-500">
                    <th className="p-3">Timestamp</th>
                    <th className="p-3">Incident Type</th>
                    <th className="p-3">Severity</th>
                  </tr>
                </thead>
                <tbody>
                  {incidents.length === 0 ? (
                    <tr><td colSpan={3} className="p-4 text-center text-slate-600">No active incidents</td></tr>
                  ) : (
                    incidents.map((inc, i) => (
                      <tr key={i} className="border-b border-slate-800 hover:bg-slate-800/30">
                        <td className="p-3 font-mono text-slate-400">{new Date(inc.timestamp).toLocaleTimeString()}</td>
                        <td className="p-3 text-red-300">{inc.incident}</td>
                        <td className="p-3"><span className="bg-red-900/30 text-red-500 px-2 py-0.5 rounded border border-red-900/50 text-xs">CRITICAL</span></td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Alerts Tab */}
      {activeTab === 'alerts' && (
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-bold mb-4 text-yellow-400">Security Alerts Feed</h3>
          <div className="space-y-2">
            {alerts.map((alert, i) => (
              <div key={i} className="flex flex-col md:flex-row justify-between items-start md:items-center bg-slate-950/50 p-4 rounded border border-slate-800 hover:border-slate-700 transition">
                <div className="flex gap-4 items-center">
                  <AlertTriangle className="w-5 h-5 text-yellow-500" />
                  <div>
                    <div className="font-bold text-slate-300">{alert.rule_name}</div>
                    <div className="text-xs text-slate-500">{alert.timestamp} | {alert.source_ip}</div>
                  </div>
                </div>
                <div className="mt-2 md:mt-0">
                  <span className={`px-2 py-1 rounded text-xs font-bold border ${getSeverityColor(alert.severity)}`}>
                    {alert.severity}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Logs Tab */}
      {activeTab === 'logs' && (
        <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
          <h3 className="text-xl font-bold mb-4 text-blue-400">Raw Log Explorer</h3>
          <div className="font-mono text-xs space-y-1">
            {logs.map((log, i) => (
              <div key={i} className="p-2 hover:bg-slate-800 rounded flex gap-4 break-all border-b border-slate-800/50">
                <span className="text-slate-500 shrink-0 w-40">{log.timestamp}</span>
                <span className="text-slate-300 grow">
                  {log.message}
                  {log.ml_anomaly && (
                    <span className="ml-2 text-purple-400">[ML Anomaly: {log.anomaly_explanation}]</span>
                  )}
                  {log.response_action && (
                    <span className="ml-2 text-red-500 font-bold">[ACTION: {log.response_action.action.toUpperCase()}]</span>
                  )}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}

function StatCard({ icon, label, value, color, isFlash }: any) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className={`p-6 rounded-xl border border-slate-800 bg-slate-900/50 flex flex-col justify-between h-32 relative overflow-hidden ${isFlash ? 'animate-pulse border-red-900 bg-red-900/10' : ''}`}
    >
      <div className="flex justify-between items-start">
        <div className={`${color}`}>{icon}</div>
        {isFlash && <div className="absolute top-0 right-0 w-full h-full bg-red-500/10 animate-ping"></div>}
      </div>
      <div>
        <h2 className="text-3xl font-bold text-slate-200">{value}</h2>
        <p className="text-xs text-slate-500 uppercase tracking-wider">{label}</p>
      </div>
    </motion.div>
  )
}

function getSeverityColor(sev: string) {
  switch (sev) {
    case 'CRITICAL': return 'bg-red-900/20 text-red-500 border-red-900';
    case 'HIGH': return 'bg-orange-900/20 text-orange-500 border-orange-900';
    case 'MEDIUM': return 'bg-yellow-900/20 text-yellow-500 border-yellow-900';
    default: return 'bg-blue-900/20 text-blue-500 border-blue-900';
  }
}
