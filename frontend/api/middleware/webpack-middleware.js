// Uses webpack dev + hot middleware

const webpack = require('webpack')
const webpackDevMiddleware = require('webpack-dev-middleware')
const webpackHotMiddleware = require('webpack-hot-middleware')
const config = require('../../webpack/webpack.config.local')

const compiler = webpack(config)

module.exports = function webpackMiddleware(app) {
  const middleware = webpackDevMiddleware(compiler, {
    publicPath: config.output.publicPath,
    stats: {
      // copied from `'minimal'`
      all: false,
      errorDetails: true,
      errors: true,
      maxModules: 0,

      // our additional options
      moduleTrace: false,

      modules: false,
      warnings: false,
    },
  })
  app.use(middleware)
  middleware.waitUntilValid(() => {
    if (process.send) {
      // Running as child process (i.e. via tests)
      // eslint-disable-next-line
            console.log('Sending completion of bundle to parent process');
      process.send({ done: true })
    }
  })
  app.use(
    webpackHotMiddleware(compiler, {
      heartbeat: 10 * 1000,
      // eslint-disable-next-line
log: console.log,
      path: '/__webpack_hmr',
    }),
  )

  return middleware
}
