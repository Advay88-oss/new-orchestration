/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
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
