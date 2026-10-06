/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Cloud Run runs the app from a container, and a standalone build ships
  // only the files the server actually needs instead of the whole
  // node_modules tree.
  output: 'standalone',
  // A build check can write elsewhere while `next dev` keeps .next.
  distDir: process.env.NEXT_DIST_DIR || '.next',
  // instrumentation.ts: the local scheduler watchdog.
  experimental: { instrumentationHook: true },
  async rewrites() {
    return [
      {
        source: '/:file(.+\\.(?:png|jpg|jpeg|mp4|webp|svg))',
        destination: '/api/media/:file',
      },
    ];
  },
};

export default nextConfig;
