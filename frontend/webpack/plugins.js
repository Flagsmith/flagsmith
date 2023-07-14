const path = require('path');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const webpack = require('webpack');

module.exports = [

    new webpack.ProvidePlugin({
        $: 'jquery',
        jQuery: 'jquery',
    }),

    new webpack.DefinePlugin({
        E2E: process.env.E2E,
        SENTRY_RELEASE_VERSION: true,
        DYNATRACE_URL: !!process.env.DYNATRACE_URL && JSON.stringify(process.env.DYNATRACE_URL)
    }),
    // // Fixes warning in moment-with-locales.min.js
    // // Module not found: Error: Can't resolve './locale' in ...
    new webpack.IgnorePlugin({
        resourceRegExp: /^\.\/locale$/,
        contextRegExp: /moment$/,
    }),
    //
    // Copy static content
    new CopyWebpackPlugin({
        patterns: [
            { from: path.join(__dirname, '../web/static'), to: path.join(__dirname, '../public/static') },
        ],
    }),
];
