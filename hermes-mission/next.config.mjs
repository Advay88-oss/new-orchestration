/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Cloud Run runs the app from a container, and a standalone build ships
  // only the files the server actually needs instead of the whole
  // node_modules tree.
  output: 'standalone',
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
