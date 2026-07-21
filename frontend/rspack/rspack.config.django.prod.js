// rspack.config.django.prod.js
// Builds files minified + cachebusted for Django

const path = require('path')
const rspack = require('@rspack/core')
const base = require('../rspack.config')
const { CopyStaticPlugin } = require('./plugins')

module.exports = {
  ...base,
  devtool: 'source-map',
  entry: {
    main: './web/main.js',
  },
  mode: 'production',
  module: {
    rules: require('./loaders')().concat([
      {
        test: /\.scss$/,
        use: [
          rspack.CssExtractRspackPlugin.loader,
          'css-loader',
          'sass-loader',
        ],
      },
    ]),
  },

  output: {
    clean: true,
    filename: '[name].[fullhash].js',
    path: path.join(__dirname, '../../api/static'),
    publicPath: '/static/',
  },

  plugins: require('./plugins')
    .concat([
      new rspack.DefinePlugin({
        SENTRY_RELEASE_VERSION: JSON.stringify(Date.now().toString()),
        __DEV__: false,
      }),

      // pull inline styles into cachebusted file
      new rspack.CssExtractRspackPlugin({
        chunkFilename: '[id].[fullhash].css',
        filename: '[name].[fullhash].css',
      }),

      // Copy static content
      new CopyStaticPlugin(
        path.join(__dirname, '../web/static'),
        path.join(__dirname, '../../api/static'),
      ),
    ])
    .concat(
      require('./pages').map(
        (page) =>
          new rspack.HtmlRspackPlugin({
            filename: `../app/templates/webpack/${page}.html`,
            template: `web/${page}.html`,
          }),
      ),
    ),
}
