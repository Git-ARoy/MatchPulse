import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  poweredByHeader: false,
  async rewrites() {
    const backendUrl =
      process.env.BACKEND_API_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      "https://matchpulse-api.salmondesert-24a13d3b.southindia.azurecontainerapps.io";
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendUrl.replace(/\/$/, "")}/api/v1/:path*`,
      },
      {
        source: "/docs",
        destination: `${backendUrl.replace(/\/$/, "")}/docs`,
      },
      {
        source: "/openapi.json",
        destination: `${backendUrl.replace(/\/$/, "")}/openapi.json`,
      },
    ];
  },
};

export default nextConfig;
