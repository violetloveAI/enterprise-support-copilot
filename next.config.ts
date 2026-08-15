import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export: single-route deterministic demo, no server runtime needed.
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
};

export default nextConfig;
