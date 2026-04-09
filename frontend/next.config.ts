import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // NOTE: Do NOT use output: "standalone" on Vercel — it breaks the deployment.
  // "standalone" is only for self-hosted Docker. Vercel manages its own output format.

  // Proxy /api/* to the FastAPI backend (Render in production, localhost in dev)
  async rewrites() {
    const backendUrl =
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
