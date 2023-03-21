// webpack.config.dev.js
const webpack = require('webpack')
const HtmlWebpackPlugin = require('html-webpack-plugin')
const path = require('path')

const base = require('./webpack.base')

module.exports = {
  ...base,
  devServer: {
    outputPath: __dirname,
  },
  devtool: 'eval-source-map',
  entry: ['webpack-hot-middleware/client?reload=false', './web/main.js'],
  mode: 'development',
  module: {
    rules: require('./loaders').concat([
      {
        test: /\.scss$/,
        use: [
          {
            loader: 'style-loader',
            options: {},
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
    devtoolModuleFilenameTemplate: 'file://[absolute-resource-path]',
    filename: '[name].js',
    path: path.join(__dirname, '../public'),
    publicPath: '/',
  },

  plugins: require('./plugins')
    .concat([
      new webpack.HotModuleReplacementPlugin(),
      new webpack.DefinePlugin({
        __DEV__: true,
        whitelabel: JSON.stringify(process.env.WHITELABEL),
      }),
      new webpack.NoEmitOnErrorsPlugin(),
      new webpack.ProvidePlugin({
        $: 'jquery',
        jQuery: 'jquery',
        jquery: 'jquery',
      }),
    ])
    .concat(
      require('./pages').map((page) => {
        // eslint-disable-next-line no-console
        console.log(page)
        return new HtmlWebpackPlugin({
          filename: `${page}.html`, // output
          template: `./web/${page}.html`, // template to use
        })
      }),
    ),
  stats: 'errors-only',
}
