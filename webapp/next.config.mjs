/**
 * Run `build` or `dev` with `SKIP_ENV_VALIDATION` to skip env validation. This is especially useful
 * for Docker builds.
 */
await import("./src/env.mjs");

/** @type {import("next").NextConfig} */
const config = {
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  experimental: {
    serverComponentsExternalPackages: ['undici', 'firebase', '@firebase/storage'],
  },
  webpack: (config, { isServer }) => {
    // Exclude undici from client-side bundling
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        undici: false,
        'node:buffer': false,
        'node:stream': false,
      };
      // Exclude these packages from being bundled on client side
      config.externals = config.externals || [];
      config.externals.push('undici', 'firebase-admin');
    }
    return config;
  },
};

export default config;
