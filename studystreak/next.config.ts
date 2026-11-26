import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
    poweredByHeader: false,
    outputFileTracingIncludes: {
        '/supplementary-analysis': ['./simulation/*.json'],
    },
    // The monorepo root has its own lockfiles; pin the workspace root to this app.
    turbopack: {
        root: import.meta.dirname,
    },
};

export default nextConfig;
