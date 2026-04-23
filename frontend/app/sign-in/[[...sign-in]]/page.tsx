import { SignIn } from "@clerk/nextjs";
import { Shield } from "lucide-react";

export default function SignInPage() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 relative">
      {/* Background glow */}
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(6,182,212,0.08)_0%,_transparent_70%)]" />
      </div>

      {/* Logo */}
      <div className="text-center mb-8 z-10">
        <Shield className="w-16 h-16 text-cyan-400 drop-shadow-[0_0_20px_rgba(34,211,238,0.6)] mx-auto mb-4" />
        <h1 className="text-5xl font-black tracking-widest text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600">
          AEGIS
        </h1>
        <p className="text-cyan-700 text-xs tracking-[0.4em] mt-1 uppercase">
          Threat Defense Command
        </p>
      </div>

      {/* Clerk SignIn with dark Aegis appearance */}
      <div className="z-10">
        <SignIn
          appearance={{
            variables: {
              colorPrimary: "#06b6d4",
              colorBackground: "#0f172a",
              colorInputBackground: "#1e293b",
              colorInputText: "#e2e8f0",
              colorText: "#e2e8f0",
              colorTextSecondary: "#64748b",
              colorNeutral: "#334155",
              borderRadius: "0.75rem",
              fontFamily: "var(--font-jetbrains-mono), monospace",
            },
            elements: {
              rootBox: "w-full",
              card: "bg-slate-900/80 border border-cyan-900/50 shadow-[0_0_60px_rgba(6,182,212,0.1)] backdrop-blur-xl",
              headerTitle: "text-cyan-300 font-bold tracking-widest uppercase text-sm",
              headerSubtitle: "text-slate-500 text-xs",
              formButtonPrimary:
                "bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 tracking-widest uppercase font-bold shadow-[0_0_20px_rgba(6,182,212,0.3)]",
              formFieldInput:
                "bg-slate-800/60 border-slate-700 focus:border-cyan-500 text-slate-200 font-mono",
              formFieldLabel: "text-slate-500 text-xs uppercase tracking-widest",
              footerActionLink: "text-cyan-500 hover:text-cyan-300",
              identityPreviewText: "text-slate-300",
              identityPreviewEditButton: "text-cyan-500",
              dividerLine: "bg-slate-800",
              dividerText: "text-slate-600",
              socialButtonsBlockButton:
                "border-slate-700 text-slate-300 hover:bg-slate-800 hover:border-cyan-900",
              socialButtonsBlockButtonText: "text-slate-300",
            },
          }}
        />
      </div>

      <p className="text-center text-xs text-slate-800 mt-6 font-mono uppercase tracking-widest z-10">
        Unauthorised access is a federal offence
      </p>
    </div>
  );
}
