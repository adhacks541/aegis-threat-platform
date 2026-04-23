"use client";
import { Shield, XCircle } from "lucide-react";
import { useClerk } from "@clerk/nextjs";

export default function UnauthorizedPage() {
  const { signOut } = useClerk();
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4">
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(239,68,68,0.06)_0%,_transparent_70%)]" />
      <div className="z-10 text-center max-w-md">
        <Shield className="w-16 h-16 text-red-500/70 mx-auto mb-6 drop-shadow-[0_0_20px_rgba(239,68,68,0.4)]" />
        <h1 className="text-4xl font-black tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-red-400 to-orange-500 mb-2">
          ACCESS DENIED
        </h1>
        <p className="text-slate-500 text-xs tracking-[0.3em] uppercase mb-8">
          Unauthorised Operator
        </p>
        <div className="bg-slate-900/80 border border-red-900/50 rounded-xl p-6 text-left font-mono text-sm mb-8">
          <div className="flex items-start gap-3 text-red-400">
            <XCircle className="w-5 h-5 mt-0.5 shrink-0" />
            <div>
              <p className="font-bold mb-1">SECURITY VIOLATION</p>
              <p className="text-slate-500 text-xs leading-relaxed">
                Your account is not authorised to access the Aegis Threat
                Defense Command. Access attempts are logged and monitored.
              </p>
            </div>
          </div>
        </div>
        <button
          onClick={() => signOut({ redirectUrl: "/sign-in" })}
          className="bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 font-bold tracking-widest uppercase text-xs px-8 py-3 rounded-lg transition-all"
        >
          Sign Out
        </button>
        <p className="text-slate-800 text-xs font-mono uppercase tracking-widest mt-6">
          Unauthorised access is a federal offence
        </p>
      </div>
    </div>
  );
}
