import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",

  // Development proxy — forwards /api/* and WebSocket /api/v1/ws/* to the
  // FastAPI backend so the browser never hits CORS issues during local dev.
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
    ];
  },
};

export default nextConfig;
