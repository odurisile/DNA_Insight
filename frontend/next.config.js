const nextConfig = {
  reactStrictMode: true,
  webpack(config) {
    // Next's filesystem pack cache can intermittently fail to rename temporary
    // files on Windows. Keep caching in memory there to avoid stale or locked
    // .next/cache/webpack pack files in both development and production builds.
    if (process.platform === "win32") {
      config.cache = { type: "memory" };
    }
    return config;
  }
};
module.exports = nextConfig;
