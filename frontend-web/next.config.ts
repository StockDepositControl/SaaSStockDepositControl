import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: [
    "192.168.1.5",
    "192.168.1.5:3001",
    "192.168.1.5:8080",
    "192.168.1.4",
    "192.168.1.4:3001",
    "192.168.1.4:8080",
    "localhost",
    "localhost:3001",
    "localhost:8080",
    "127.0.0.1",
    "127.0.0.1:3001",
    "127.0.0.1:8080",
  ],
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: "http://127.0.0.1:8000/api/v1/:path*",
      },
    ];
  },
};

export default nextConfig;
