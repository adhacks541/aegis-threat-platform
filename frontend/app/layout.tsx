import type { Metadata } from "next";
import { Orbitron, JetBrains_Mono } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import "./globals.css";

const orbitron = Orbitron({
  variable: "--font-orbitron",
  subsets: ["latin"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Aegis SIEM - Intelligent Threat Defense",
  description: "Advanced AI-Powered Security Information & Event Management",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider
      signInUrl="/sign-in"
      signUpUrl="/sign-up"
      appearance={{
        variables: {
          colorPrimary: "#06b6d4",
          colorBackground: "#0f172a",
          colorInputBackground: "#1e293b",
          colorInputText: "#e2e8f0",
          colorText: "#e2e8f0",
          colorTextSecondary: "#94a3b8",
          colorNeutral: "#e2e8f0",
        },
      }}
    >
      <html lang="en" className="dark">
        <body
          className={`${orbitron.variable} ${jetbrainsMono.variable} antialiased bg-slate-950 text-slate-200 overflow-x-hidden selection:bg-cyan-500/30 selection:text-cyan-200`}
        >
          <div className="fixed inset-0 z-[-1] bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-slate-900 via-[#020617] to-black opacity-80 pointer-events-none" />
          <div className="fixed inset-0 z-[-1] bg-cyber-grid pointer-events-none opacity-20" />
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
