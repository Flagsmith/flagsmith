// webpack.config.prod.js
// Watches + deploys files minified + cachebusted

const path = require('path')
const webpack = require('webpack')
const HtmlWebpackPlugin = require('html-webpack-plugin')
const CleanWebpackPlugin = require('clean-webpack-plugin')
const CopyWebpackPlugin = require('copy-webpack-plugin')
const TerserPlugin = require('terser-webpack-plugin')
const moment = require('moment')
const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const base = require('./webpack.base')

module.exports = {
  ...base,
  devtool: 'source-map',
  entry: {
    main: './web/main.js',
  },
  mode: 'production',
  module: {
    rules: require('./loaders').concat([
      {
        test: /\.scss$/,
        use: [MiniCssExtractPlugin.loader, 'css-loader', 'sass-loader'],
      },
    ]),
  },
  optimization: {
    // chunk bundle into Libraries, App JS and dumb components
    minimizer: [
      new TerserPlugin({
        extractComments: true,
        parallel: true,
      }),
    ],
  },

  output: {
    filename: '[name].[fullhash].js',
    path: path.join(__dirname, '../../api/static'),
    publicPath: '/static/',
  },

  plugins: require('./plugins')
    .concat([
      // Clear out the static django build folder
      new CleanWebpackPlugin(['static'], {
        root: path.join(__dirname, '../../api'),
      }),

      new webpack.DefinePlugin({
        SENTRY_RELEASE_VERSION: moment().valueOf().toString(),
        __DEV__: false,
      }),

      // pull inline styles into cachebusted file
      new MiniCssExtractPlugin({
        chunkFilename: '[id].[fullhash].css',
        filename: '[name].[fullhash].css',
      }),

      // Copy static content
      new CopyWebpackPlugin({
        patterns: [
          {
            from: path.join(__dirname, '../web/static'),
            to: path.join(__dirname, '../../api/static'),
          },
        ],
      }),
    ])
    .concat(
      require('./pages').map(
        (page) =>
          new HtmlWebpackPlugin({
            // template to use
            'assets': {
              // add these script/link tags
              'client': '/[fullhash].js',
              'style': 'style.[fullhash].css',
            },

            filename: `${page}.html`,
            // output template
            template: `../api/app/templates/${page}.html`,
          }),
      ),
    ),
}
