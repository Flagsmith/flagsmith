// Uses webpack dev + hot middleware

const webpack = require('webpack');
const webpackDevMiddleware = require('webpack-dev-middleware');
const webpackHotMiddleware = require('webpack-hot-middleware');
const config = require('../../webpack/webpack.config.local');

const compiler = webpack(config);


module.exports = function (app) {
    const middleware = webpackDevMiddleware(compiler, {
        publicPath: config.output.publicPath,
        stats: {
            // copied from `'minimal'`
            all: false,
            modules: false,
            maxModules: 0,
            errors: true,
            warnings: false,
            // our additional options
            moduleTrace: false,
            errorDetails: true,
        },
    });
    app.use(middleware);
    middleware.waitUntilValid(() => {
        if (process.send) { // Running as child process (i.e. via tests)
            console.log('Sending completion of bundle to parent process');
            process.send({ done: true });
        }
    });
    app.use(webpackHotMiddleware(compiler, {
        log: console.log,
        path: '/__webpack_hmr',
        heartbeat: 10 * 1000,
    }));

    return middleware;
};
