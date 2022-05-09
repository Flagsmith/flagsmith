// webpack.config.prod.js
// Watches + deploys files minified + cachebusted

const url = require('url');
const path = require('path');
const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const TerserPlugin = require('terser-webpack-plugin');
const moment = require('moment');

const Project = require('../common/project');

const extraPlugins = [
    // Clear out build folder
    new CleanWebpackPlugin(['public'], { root: path.join(__dirname, '../') }),
    new MiniCssExtractPlugin({
        filename:  "[name].[fullhash].css",
        chunkFilename:  "[id].[fullhash].css",
    }),
    new webpack.DefinePlugin({
        __DEV__: false,
        SENTRY_RELEASE_VERSION: moment().valueOf().toString(),
    }),
];


module.exports = {
    devtool: process.env.E2E ? false : 'source-map',
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
    externals: {
        // require('jquery') is external and available
        //  on the global var jQuery
        'jquery': 'jQuery',
    },
    output: {
        path: path.join(__dirname, '../public/static'),
        filename: '[name].[fullhash].js',
        publicPath: "/static/"
    },

    plugins: require('./plugins')
        .concat(extraPlugins).concat(require('./pages').map((page) => {
            console.log(page);
            return new HtmlWebpackPlugin({
                filename: `${page}.handlebars`, // output
                template: `./web/${page}.handlebars`, // template to use
                'assets': { // add these script/link tags
                    'client': '/[fullhash].js',
                    'style': 'style.[fullhash].css',
                },
            });
        })),

    module: {
        rules: require('./loaders').concat([
            {
                test: /\.scss$/,
                use: [MiniCssExtractPlugin.loader, 'css-loader','sass-loader'],
            },
        ]),
    },
};
