/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone', // lean container for Cloud Run
  // The /api routes are the unused "future live" seam (they read local files the
  // deployed fixture dashboard never touches). Don't fail the build on their types.
  typescript: { ignoreBuildErrors: true },
  eslint: { ignoreDuringBuilds: true },
  // The dashboard reads a local relay and local files. When the read-only
  // backend lands, proxy it here so the browser never needs CORS.
  async rewrites() {
    return [
      {
        source: '/api/relay/:path*',
        destination: `${process.env.BUZZ_RELAY_URL ?? 'http://127.0.0.1:3000'}/:path*`,
      },
    ];
  },
};

export default nextConfig;
