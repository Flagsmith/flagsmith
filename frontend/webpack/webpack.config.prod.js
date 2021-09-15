// webpack.config.prod.js
// Watches + deploys files minified + cachebusted

const url = require('url');
const path = require('path');
const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const UglifyJSPlugin = require('uglifyjs-webpack-plugin');
const moment = require('moment');

const Project = require('../common/project');

const extraPlugins = [
    // Clear out build folder
    new CleanWebpackPlugin(['build'], { root: path.join(__dirname, '../') }),

    new webpack.DefinePlugin({
        __DEV__: false,
        SENTRY_RELEASE_VERSION: moment().valueOf().toString(),
    }),
];
if (!process.env.E2E) {
    // reduce filesize
    extraPlugins.push(new webpack.optimize.OccurrenceOrderPlugin());
    extraPlugins.push(new ExtractTextPlugin({ filename: 'style.[hash].css', allChunks: true }));
} else {
    extraPlugins.push(new ExtractTextPlugin({ filename: 'style.[hash].css', allChunks: true }));
}
module.exports = {
    devtool: process.env.E2E ? false : 'source-map',
    mode: 'production',

    entry: {
        main: './web/main.js',
    },
    optimization: { // chunk bundle into Libraries, App JS and dumb components
        minimizer: process.env.E2E ? [] : [
            new UglifyJSPlugin({
                cache: !process.env.E2E,
                parallel: true,
                sourceMap: !process.env.E2E, // set to true if you want JS source maps
                extractComments: !process.env.E2E,
                uglifyOptions: process.env.E2E ? null : {
                    compress: {
                        drop_console: true,
                    },
                },
            }),
        ],
    },
    externals: {
        // require('jquery') is external and available
        //  on the global var jQuery
        'jquery': 'jQuery',
    },
    output: {
        path: path.join(__dirname, '../build/static'),
        filename: '[name].[hash].js',
        publicPath: url.resolve(process.env.ASSET_URL || Project.assetUrl || 'https://cdn.flagsmith.com', 'static/'),
    },

    plugins: require('./plugins')
        .concat(extraPlugins).concat(require('./pages').map((page) => {
            console.log(page);
            return new HtmlWebpackPlugin({
                filename: `${page}.handlebars`, // output
                template: `./web/${page}.handlebars`, // template to use
                'assets': { // add these script/link tags
                    'client': '/[hash].js',
                    'style': 'style.[hash].css',
                },
            });
        })),

    module: {
        rules: require('./loaders').concat([
            {
                test: /\.scss$/,
                use: ExtractTextPlugin.extract({ fallback: 'style-loader', use: 'css-loader!sass-loader' }),
            },
        ]),
    },
};
