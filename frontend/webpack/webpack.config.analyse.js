// webpack.config.analyse.js
// Breaks down the bundle size of our production config using webpack-bundle-analyzer
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;
const baseConfig = require('./webpack.config.prod');

module.exports = {
    ...baseConfig,
    plugins: baseConfig.plugins.concat([new BundleAnalyzerPlugin()]),
};
