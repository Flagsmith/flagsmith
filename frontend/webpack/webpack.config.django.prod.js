// webpack.config.prod.js
// Watches + deploys files minified + cachebusted

const path = require('path');
const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const TerserPlugin = require('terser-webpack-plugin');
const moment = require('moment');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const base = require('../webpack.config');

module.exports = {
    ...base,
    devtool: 'source-map',
    mode: 'production',
    entry: {
        main: './web/main.js',
    },
    optimization: { // chunk bundle into Libraries, App JS and dumb components
        minimizer: [
            new TerserPlugin({
                parallel: true,
                extractComments: true,
            }),
        ],
    },
    output: {
        path: path.join(__dirname, '../../api/static'),
        publicPath: '/static/',
        filename: '[name].[fullhash].js',
    },

    plugins: require('./plugins')
        .concat([
            // Clear out the static django build folder
            new CleanWebpackPlugin(['static'], { root: path.join(__dirname, '../../api') }),

            new webpack.DefinePlugin({
                __DEV__: false,
                SENTRY_RELEASE_VERSION: moment().valueOf().toString(),
            }),

            // pull inline styles into cachebusted file
            new MiniCssExtractPlugin({
                filename: '[name].[fullhash].css',
                chunkFilename: '[id].[fullhash].css',
            }),

            // Copy static content
            new CopyWebpackPlugin(
                {
                    patterns: [
                        { from: path.join(__dirname, '../web/static'), to: path.join(__dirname, '../../api/static') },
                    ],
                },
            ),

        ]).concat(require('./pages').map(page => new HtmlWebpackPlugin({
            filename: `../app/templates/webpack/${page}.html`, // output template (relative from static dir)
            template: `web/${page}.html`, // template to use (use the same template used for running FE outside of vercel)
            'assets': { // add these script/link tags
                'client': '/[fullhash].js',
                'style': 'style.[fullhash].css',
            },
        }))),

    module: {
        rules: require('./loaders').concat([
            {
                test: /\.scss$/,
                use: [MiniCssExtractPlugin.loader, 'css-loader', 'sass-loader'],
            },
        ]),
    },
};
