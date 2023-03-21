// webpack.config.prod.js
// Watches + deploys files minified + cachebusted

const path = require('path')
const webpack = require('webpack')
const HtmlWebpackPlugin = require('html-webpack-plugin')
const MiniCssExtractPlugin = require('mini-css-extract-plugin')
const CleanWebpackPlugin = require('clean-webpack-plugin')
const TerserPlugin = require('terser-webpack-plugin')
const moment = require('moment')
const base = require('./webpack.base')

const extraPlugins = [
  // Clear out build folder
  new CleanWebpackPlugin(['public'], { root: path.join(__dirname, '../') }),
  new MiniCssExtractPlugin({
    chunkFilename: '[id].[fullhash].css',
    filename: '[name].[fullhash].css',
  }),
  new webpack.DefinePlugin({
    SENTRY_RELEASE_VERSION: moment().valueOf().toString(),
    __DEV__: false,
  }),
]

module.exports = {
  ...base,
  devtool: process.env.E2E ? false : 'source-map',
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
    path: path.join(__dirname, '../public/static'),
    publicPath: '/static/',
  },

  plugins: require('./plugins')
    .concat(extraPlugins)
    .concat(
      require('./pages').map((page) => {
        // eslint-disable-next-line no-console
        console.log(page)
        return new HtmlWebpackPlugin({
          // template to use
          'assets': {
            // add these script/link tags
            'client': '/[fullhash].js',
            'style': 'style.[fullhash].css',
          },

          filename: `${page}.handlebars`,
          // output
          template: `./web/${page}.handlebars`,
        })
      }),
    ),
}
