"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line
} from "recharts";
import { Activity, ShieldAlert, Globe, Radio, Server } from "lucide-react";

// Types
interface Stats {
  total_logs: number;
  high_alerts: number;
  critical_incidents: number;
}

interface LogActivity {
  name: string;
  logs: number;
}

interface Alert {
  timestamp: string;
  message: string;
  severity: string;
  source: string;
  ip?: string;
}

const API_URL = "http://localhost:8000/api/v1/dashboard";

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [activity, setActivity] = useState<LogActivity[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [statsRes, activityRes, alertsRes] = await Promise.all([
        axios.get(`${API_URL}/stats`),
        axios.get(`${API_URL}/activity`),
        axios.get(`${API_URL}/recent`),
      ]);
      setStats(statsRes.data);
      setActivity(activityRes.data);
      setAlerts(alertsRes.data);
    } catch (error) {
      console.error("Failed to fetch dashboard data", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, []);

  if (loading && !stats) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-950 text-emerald-500 font-mono">
        <Activity className="animate-pulse mr-2" /> INITIALIZING AEGIS SYSTEM...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-emerald-500/30">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-8 h-8 text-emerald-500" />
            <h1 className="text-xl font-bold tracking-tight">
              AEGIS <span className="text-slate-500 font-light">SIEM</span>
            </h1>
          </div>
          <div className="flex items-center gap-4 text-xs font-mono text-emerald-500/80">
            <div className="flex items-center gap-1.5">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              SYSTEM ONLINE
            </div>
            <div>WS: CONNECTED</div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8 space-y-8">
        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card title="Total Events Processed" icon={<Server className="w-5 h-5 text-blue-400" />} value={stats?.total_logs} color="blue" />
          <Card title="High Severity Alerts" icon={<Radio className="w-5 h-5 text-orange-400" />} value={stats?.high_alerts} color="orange" />
          <Card title="Critical Incidents" icon={<ShieldAlert className="w-5 h-5 text-red-500" />} value={stats?.critical_incidents} color="red" isFlash={(stats?.critical_incidents || 0) > 0} />
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Timeline Chart */}
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl">
            <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
              <Activity className="w-4 h-4 text-slate-400" /> Event Volume (Last 24h)
            </h3>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={activity}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                  <YAxis stroke="#64748b" fontSize={12} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#1e293b', color: '#f8fafc' }}
                    itemStyle={{ color: '#10b981' }}
                    cursor={{ fill: '#1e293b', opacity: 0.4 }}
                  />
                  <Bar dataKey="logs" fill="#3b82f6" radius={[4, 4, 0, 0]} maxBarSize={40} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Recent Alerts Feed */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl overflow-hidden flex flex-col">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-red-500" /> Live Threat Feed
            </h3>
            <div className="flex-1 overflow-y-auto space-y-3 pr-2 scrollbar-thin scrollbar-thumb-slate-700">
              {alerts.length === 0 ? (
                <div className="text-slate-500 text-center py-10 italic">No active threats detected.</div>
              ) : (
                alerts.map((alert, i) => (
                  <div key={i} className={`p-3 rounded-lg border text-sm ${alert.severity === 'CRITICAL' ? 'bg-red-950/20 border-red-900/50 text-red-200' :
                      alert.severity === 'HIGH' ? 'bg-orange-950/20 border-orange-900/50 text-orange-200' :
                        'bg-slate-800 border-slate-700 text-slate-300'
                    }`}>
                    <div className="flex justify-between items-start mb-1">
                      <span className={`font-bold text-xs px-1.5 py-0.5 rounded ${alert.severity === 'CRITICAL' ? 'bg-red-500 text-white' : 'bg-orange-500 text-white'
                        }`}>{alert.severity}</span>
                      <span className="text-xs text-slate-500 font-mono">{new Date(alert.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div className="font-medium text-xs mb-1">{alert.message}</div>
                    <div className="flex items-center gap-3 text-[10px] text-slate-500 uppercase tracking-wider">
                      <span>SRC: {alert.source}</span>
                      {alert.ip && <span>IP: {alert.ip}</span>}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Map Section Placeholder (Leaflet needs CSR carefully) */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl h-[400px] flex items-center justify-center relative overflow-hidden group">
          <div className="absolute inset-0 bg-[url('https://upload.wikimedia.org/wikipedia/commons/e/ec/World_map_blank_without_borders.svg')] bg-cover opacity-5 grayscale group-hover:opacity-10 transition-opacity"></div>
          <div className="text-center z-10">
            <Globe className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <h3 className="text-lg font-semibold text-slate-400">Global Attack Map</h3>
            <p className="text-sm text-slate-500">Visualization of GeoIP sources</p>
            <p className="text-xs text-slate-600 mt-2">(Leaflet Integration Pending Phase 6 Completion)</p>
          </div>
        </div>
      </main>
    </div>
  );
}

function Card({ title, value, icon, color, isFlash }: any) {
  return (
    <div className={`p-6 rounded-xl border bg-slate-900 shadow-lg relative overflow-hidden ${isFlash ? 'animate-pulse-slow border-red-500/50' : 'border-slate-800'}`}>
      <div className={`absolute top-0 right-0 w-24 h-24 bg-${color}-500/10 rounded-full -mr-12 -mt-12 blur-2xl`}></div>
      <div className="flex justify-between items-start mb-4 relative z-10">
        <div className="text-slate-400 text-sm font-medium">{title}</div>
        <div className={`p-2 rounded-lg bg-${color}-500/10`}>{icon}</div>
      </div>
      <div className="text-3xl font-bold text-slate-100 font-mono relative z-10">
        {value?.toLocaleString() || 0}
      </div>
    </div>
  );
}
