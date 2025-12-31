/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable rewrites for Python API routes
  async rewrites() {
    return [];
  },
};

module.exports = nextConfig;
