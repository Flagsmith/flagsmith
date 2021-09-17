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

module.exports = {
    devtool: 'source-map',
    mode: 'production',

    entry: {
        main: './web/main.js',
    },
    optimization: { // chunk bundle into Libraries, App JS and dumb components
        minimizer: [
            new UglifyJSPlugin({
                cache: true,
                parallel: true,
                sourceMap: true, // set to true if you want JS source maps
                extractComments: true,
                uglifyOptions: {
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
        publicPath: url.resolve(process.env.STATIC_ASSET_CDN_URL || Project.assetUrl || 'https://cdn.flagsmith.com', 'static/'),
    },

    plugins: require('./plugins')
        .concat([
            // Clear out build folder
            new CleanWebpackPlugin(['build'], { root: path.join(__dirname, '../') }),

            new webpack.DefinePlugin({
                __DEV__: false,
                SENTRY_RELEASE_VERSION: moment().valueOf().toString(),
            }),

            // reduce filesize
            new webpack.optimize.OccurrenceOrderPlugin(),

            // pull inline styles into cachebusted file
            new ExtractTextPlugin({ filename: 'style.[hash].css', allChunks: true }),

        ]).concat(require('./pages').map((page) => {
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
