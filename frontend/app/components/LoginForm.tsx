"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Shield, Lock, Eye, EyeOff, AlertCircle } from "lucide-react";

interface LoginFormProps {
  onSuccess: (token: string) => void;
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function LoginForm({ onSuccess }: LoginFormProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const form = new URLSearchParams();
      form.append("username", username);
      form.append("password", password);

      const res = await fetch(`${API_BASE}/api/v1/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: form.toString(),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Authentication failed");
      }

      const data = await res.json();
      localStorage.setItem("aegis_token", data.access_token);
      onSuccess(data.access_token);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative">
      {/* Animated grid background */}
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(6,182,212,0.08)_0%,_transparent_70%)]" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 30, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
        className="relative z-10 w-full max-w-md"
      >
        {/* Logo */}
        <div className="text-center mb-10">
          <motion.div
            animate={{ rotate: [0, 5, -5, 0] }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            className="inline-block mb-4"
          >
            <Shield className="w-20 h-20 text-cyan-400 drop-shadow-[0_0_20px_rgba(34,211,238,0.6)] mx-auto" />
          </motion.div>
          <h1 className="text-5xl font-black tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600">
            AEGIS
          </h1>
          <p className="text-cyan-700 text-xs tracking-[0.4em] mt-1 uppercase">
            Threat Defense Command
          </p>
        </div>

        {/* Login card */}
        <div className="bg-slate-900/80 backdrop-blur-xl border border-cyan-900/50 rounded-2xl p-8 shadow-[0_0_60px_rgba(6,182,212,0.1)]">
          <h2 className="text-slate-300 text-sm font-bold uppercase tracking-widest mb-6 flex items-center gap-2">
            <Lock className="w-4 h-4 text-cyan-500" />
            Secure Authentication
          </h2>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Username */}
            <div>
              <label className="block text-xs text-slate-500 uppercase tracking-widest mb-2">
                Operator ID
              </label>
              <input
                id="aegis-username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                required
                className="w-full bg-slate-800/60 border border-slate-700 focus:border-cyan-500 rounded-lg px-4 py-3 text-slate-200 font-mono text-sm outline-none transition-all duration-200 focus:shadow-[0_0_0_2px_rgba(6,182,212,0.2)] placeholder-slate-600"
                placeholder="operator_id"
              />
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs text-slate-500 uppercase tracking-widest mb-2">
                Access Key
              </label>
              <div className="relative">
                <input
                  id="aegis-password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                  className="w-full bg-slate-800/60 border border-slate-700 focus:border-cyan-500 rounded-lg px-4 py-3 pr-12 text-slate-200 font-mono text-sm outline-none transition-all duration-200 focus:shadow-[0_0_0_2px_rgba(6,182,212,0.2)] placeholder-slate-600"
                  placeholder="••••••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-cyan-400 transition-colors"
                >
                  {showPassword ? (
                    <EyeOff className="w-4 h-4" />
                  ) : (
                    <Eye className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Error */}
            {error && (
              <motion.div
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-center gap-2 text-red-400 bg-red-950/40 border border-red-500/30 rounded-lg px-4 py-3 text-sm"
              >
                <AlertCircle className="w-4 h-4 shrink-0" />
                {error}
              </motion.div>
            )}

            {/* Submit */}
            <button
              id="aegis-login-btn"
              type="submit"
              disabled={loading}
              className="w-full relative overflow-hidden bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold tracking-widest uppercase py-3 rounded-lg transition-all duration-300 shadow-[0_0_20px_rgba(6,182,212,0.3)] hover:shadow-[0_0_30px_rgba(6,182,212,0.5)]"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Authenticating…
                </span>
              ) : (
                "Initialize Session"
              )}
            </button>
          </form>

          <p className="text-center text-xs text-slate-700 mt-6 font-mono">
            ENCRYPTED CHANNEL · TLS 1.3 · JWT
          </p>
        </div>

        <p className="text-center text-xs text-slate-800 mt-4 font-mono uppercase tracking-widest">
          Unauthorised access is a federal offence
        </p>
      </motion.div>
    </div>
  );
}
