const path = require('path')

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8003',
  },
  webpack: (config) => {
    // Explicitly set alias for @ to point to project root
    const rootPath = path.resolve(__dirname)
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': rootPath,
    }
    
    // Ensure extensions are resolved
    config.resolve.extensions = [
      '.js',
      '.jsx',
      '.ts',
      '.tsx',
      '.json',
      ...(config.resolve.extensions || []),
    ]
    
    return config
  },
}

module.exports = nextConfig

