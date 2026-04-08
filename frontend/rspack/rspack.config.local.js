// rspack.config.local.js (dev)
const rspack = require('@rspack/core')
const ReactRefreshPlugin = require('@rspack/plugin-react-refresh')
const path = require('path')

const base = require('../rspack.config')

module.exports = {
  ...base,
  devServer: {
    historyApiFallback: true,
    hot: true,
    liveReload: false,
    port: process.env.PORT || 8080,
    setupMiddlewares: (middlewares, devServer) => {
      // Register the Express routes from api/index on the dev server's app
      require('../api/dev-routes')(devServer.app)
      return middlewares
    },
    static: {
      directory: path.join(__dirname, '../web/static'),
      publicPath: '/static/',
      watch: false,
    },
  },
  devtool: 'eval-source-map',
  entry: ['./web/main.js'],
  mode: 'development',
  module: {
    rules: require('./loaders')(true).concat([
      {
        test: /\.scss$/,
        use: [
          {
            loader: 'style-loader',
          },
          {
            loader: 'css-loader',
            options: {
              importLoaders: 1,
              sourceMap: true,
            },
          },
          {
            loader: 'sass-loader',
            options: {
              sourceMap: true,
            },
          },
        ],
      },
    ]),
  },
  output: {
    filename: '[name].js',
    path: path.join(__dirname, '../public'),
    publicPath: '/',
  },
  plugins: require('./plugins')
    .concat([
      new ReactRefreshPlugin(),
      new rspack.DefinePlugin({
        SENTRY_RELEASE_VERSION: JSON.stringify(''),
        __DEV__: true,
        whitelabel: JSON.stringify(process.env.WHITELABEL),
      }),
      // Note: HotModuleReplacementPlugin is not needed — devServer.hot: true handles it
    ])
    .concat(
      require('./pages').map((page) => {
        // eslint-disable-next-line no-console
        console.log(page)
        return new rspack.HtmlRspackPlugin({
          filename: `${page}.html`,
          template: `./web/${page}.html`,
        })
      }),
    ),
  stats: 'errors-only',
}
