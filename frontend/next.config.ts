import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Vercel supports standalone mode natively. Also needed for Docker self-hosting.
  output: "standalone",

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
