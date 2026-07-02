import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Standalone output bundles only what's needed for production,
  // making the Docker image significantly smaller.
  output: "standalone",

  // Disable x-powered-by header for security
  poweredByHeader: false,
};

export default nextConfig;
