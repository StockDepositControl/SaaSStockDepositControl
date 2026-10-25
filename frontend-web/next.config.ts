import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  allowedDevOrigins: [
    "localhost",
    "localhost:3001",
    "localhost:8080",
    "127.0.0.1",
    "127.0.0.1:3001",
    "127.0.0.1:8080",
  ],
};

export default nextConfig;
