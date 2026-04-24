// Proxy any request the Next app does not itself serve (e.g. /api/*, /health,
// /metrics, and any unknown URL) to the Flask API. This lets peer reviewers
// submit a single domain — the frontend — and still hit every documented
// endpoint, while also giving the browser a same-origin /api/* to call.
const API_BASE = (
  process.env.NEXT_PUBLIC_API_URL || "https://job-market-trend-analyzer.fly.dev"
).replace(/\/$/, "")

/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return {
      beforeFiles: [
        { source: "/api/:path*", destination: `${API_BASE}/api/:path*` },
        { source: "/health", destination: `${API_BASE}/health` },
        { source: "/metrics", destination: `${API_BASE}/metrics` },
      ],
      afterFiles: [],
      fallback: [
        { source: "/:path*", destination: `${API_BASE}/:path*` },
      ],
    }
  },
}

export default nextConfig
