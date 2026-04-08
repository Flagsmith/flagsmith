// rspack.config.prod.js
// Builds files minified + cachebusted

const path = require('path')
const rspack = require('@rspack/core')
const HtmlWebpackPlugin = require('html-webpack-plugin')
const { sentryWebpackPlugin } = require('@sentry/webpack-plugin')
const base = require('../rspack.config')

const extraPlugins = [
  new rspack.CssExtractRspackPlugin({
    chunkFilename: '[id].[fullhash].css',
    filename: '[name].[fullhash].css',
  }),
  new rspack.DefinePlugin({
    SENTRY_RELEASE_VERSION: JSON.stringify(Date.now().toString()),
    __DEV__: false,
  }),
]

module.exports = {
  ...base,
  devtool: process.env.E2E ? false : 'source-map',
  entry: {
    main: './web/main.js',
  },
  ignoreWarnings: [
    /Critical dependency: the request of a dependency is an expression/, // framer-motion
    /Module not found: Can't resolve '\.\/locale'/, // moment
  ],
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
    path: path.join(__dirname, '../public/static'),
    publicPath: '/static/',
  },

  performance: {
    hints: false,
  },

  plugins: require('./plugins')
    .concat(extraPlugins)
    .concat(
      require('./pages').map((page) => {
        // eslint-disable-next-line no-console
        console.log(page)
        // Use html-webpack-plugin (Rspack-compatible) to preserve Handlebars {{}} syntax
        return new HtmlWebpackPlugin({
          'assets': {
            'client': '/[fullhash].js',
            'style': 'style.[fullhash].css',
          },
          filename: `${page}.handlebars`,
          template: `./web/${page}.handlebars`,
        })
      }),
    )
    .concat(
      process.env.SENTRY_AUTH_TOKEN
        ? [
            sentryWebpackPlugin({
              authToken: process.env.SENTRY_AUTH_TOKEN,
              org: 'flagsmith',
              project: 'flagsmith-frontend',
            }),
          ]
        : [],
    ),
}
