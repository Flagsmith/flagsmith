const path = require('path');
const fs = require('fs');
const webpack = require('webpack');

class CopyStaticPlugin {
    constructor(src, dest) {
        this.src = src;
        this.dest = dest;
    }

    apply(compiler) {
        compiler.hooks.afterEmit.tap('CopyStaticPlugin', () => {
            try {
                fs.cpSync(this.src, this.dest, { recursive: true });
            } catch (error) {
                compiler.errors.push(
                    new Error(`CopyStaticPlugin: Failed to copy ${this.src} to ${this.dest}: ${error.message}`)
                );
            }        
         });
    }
}

const plugins = [

    new webpack.DefinePlugin({
        SENTRY_RELEASE_VERSION: true,
    }),
    // // Fixes warning in moment-with-locales.min.js
    // // Module not found: Error: Can't resolve './locale' in ...
    new webpack.IgnorePlugin({
        resourceRegExp: /^\.\/locale$/,
        contextRegExp: /moment$/,
    }),
    // Copy static content
    new CopyStaticPlugin(
        path.join(__dirname, '../web/static'),
        path.join(__dirname, '../public/static'),
    ),
];

plugins.CopyStaticPlugin = CopyStaticPlugin;

module.exports = plugins;
