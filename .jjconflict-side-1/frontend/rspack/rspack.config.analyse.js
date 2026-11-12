// rspack.config.analyse.js
// Breaks down the bundle size using webpack-bundle-analyzer
const BundleAnalyzerPlugin =
  require('webpack-bundle-analyzer').BundleAnalyzerPlugin
const baseConfig = require('./rspack.config.prod')

module.exports = {
  ...baseConfig,
  plugins: baseConfig.plugins.concat([new BundleAnalyzerPlugin()]),
}
