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
              colorTextSecondary: "#94a3b8",
              colorTextOnPrimaryBackground: "#ffffff",
              colorNeutral: "#e2e8f0",
              colorDanger: "#f87171",
              borderRadius: "0.75rem",
              fontFamily: "var(--font-jetbrains-mono), monospace",
            },
            elements: {
              rootBox: "w-full max-w-md",
              card: "bg-slate-900/90 border border-cyan-900/40 shadow-[0_0_60px_rgba(6,182,212,0.08)] backdrop-blur-xl !text-slate-200",
              // Header
              headerTitle: "!text-cyan-300 font-bold tracking-widest uppercase text-sm",
              headerSubtitle: "!text-slate-400 text-xs",
              // Form
              formFieldLabel: "!text-slate-400 text-xs uppercase tracking-widest",
              formFieldInput:
                "!bg-slate-800/70 !border-slate-700 focus:!border-cyan-500 !text-slate-100 font-mono placeholder:!text-slate-600",
              formFieldHintText: "!text-slate-500",
              formFieldSuccessText: "!text-emerald-400",
              formFieldErrorText: "!text-red-400",
              formFieldWarningText: "!text-amber-400",
              formButtonPrimary:
                "!bg-gradient-to-r !from-cyan-600 !to-blue-600 hover:!from-cyan-500 hover:!to-blue-500 tracking-widest uppercase font-bold shadow-[0_0_20px_rgba(6,182,212,0.3)] !text-white",
              formButtonReset: "!text-cyan-400 hover:!text-cyan-300",
              // Social buttons
              socialButtonsBlockButton:
                "!border-slate-700 !text-slate-200 hover:!bg-slate-800 hover:!border-cyan-900/50 !bg-slate-800/50",
              socialButtonsBlockButtonText: "!text-slate-200 font-medium",
              socialButtonsBlockButtonArrow: "!text-slate-400",
              socialButtonsProviderIcon: "brightness-110",
              // Divider
              dividerLine: "!bg-slate-700",
              dividerText: "!text-slate-500",
              // Footer
              footerAction: "!text-slate-400",
              footerActionText: "!text-slate-400",
              footerActionLink: "!text-cyan-400 hover:!text-cyan-300 font-semibold",
              footerPages: "!text-slate-500",
              footerPagesLink: "!text-slate-400",
              // Identity preview
              identityPreview: "!bg-slate-800/50 !border-slate-700",
              identityPreviewText: "!text-slate-200",
              identityPreviewEditButton: "!text-cyan-400 hover:!text-cyan-300",
              identityPreviewEditButtonIcon: "!text-cyan-400",
              // Internal card
              cardBox: "!bg-transparent",
              main: "!text-slate-200",
              // Alert / badge
              badge: "!text-slate-300 !bg-slate-800 !border-slate-700",
              alert: "!text-slate-200 !bg-slate-800/50 !border-slate-700",
              alertText: "!text-slate-200",
              // OTP
              otpCodeFieldInput: "!bg-slate-800 !border-slate-600 !text-slate-100",
              // User button / profile
              userButtonPopoverCard: "!bg-slate-900 !border-slate-700",
              userButtonPopoverActionButton: "!text-slate-200",
              userButtonPopoverFooter: "!text-slate-500",
              // Misc text that Clerk injects
              formHeaderTitle: "!text-slate-200",
              formHeaderSubtitle: "!text-slate-400",
              alternativeMethodsBlockButton: "!text-slate-300 !border-slate-700 hover:!bg-slate-800",
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
