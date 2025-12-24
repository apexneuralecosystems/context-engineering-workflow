const path = require('path')

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
  },
  webpack: (config) => {
    const rootPath = path.resolve(__dirname)
    
    // Set up aliases
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': rootPath,
    }
    
    // Ensure proper module resolution
    config.resolve.modules = [
      rootPath,
      path.resolve(rootPath, 'node_modules'),
      'node_modules',
    ]
    
    // Ensure extensions are resolved in order
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

