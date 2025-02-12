// webpack.config.dev.js
const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const path = require('path');

const base = require('../webpack.config');
const ReactRefreshWebpackPlugin = require('@pmmmwh/react-refresh-webpack-plugin');

module.exports = {
    ...base,
    devtool: 'eval-source-map',
    mode: 'development',
    stats: 'errors-only',
    entry: [
        'webpack-hot-middleware/client?reload=false',
        './web/main.js',
    ],
    devServer: {
        hot: true,
        outputPath: __dirname,
    },
    output: {
        path: path.join(__dirname, '../public'),
        filename: '[name].js',
        publicPath: '/',
        devtoolModuleFilenameTemplate: 'file://[absolute-resource-path]',
    },

    plugins: require('./plugins').concat([
        new webpack.HotModuleReplacementPlugin(),
        new ReactRefreshWebpackPlugin(),
        new webpack.DefinePlugin({
            __DEV__: true,
            whitelabel: JSON.stringify(process.env.WHITELABEL),
        }),
        new webpack.NoEmitOnErrorsPlugin(),
    ]).concat(require('./pages').map((page) => {
        // eslint-disable-next-line no-console
        console.log(page);
        return new HtmlWebpackPlugin({
            filename: `${page}.html`, // output
            template: `./web/${page}.html`, // template to use
        });
    })),
    module: {
        rules: require('./loaders')
            .concat([
                {
                    test: /\.scss$/,
                    use: [{
                        loader: 'style-loader',
                        options: {
                        },
                    },
                    {
                        loader: 'css-loader',
                        options: {
                            importLoaders: 1,
                            sourceMap: true,
                        },
                    }, {
                        loader: 'sass-loader',
                        options: {
                            sourceMap: true,
                        },
                    }],
                },
            ]),
    },
};
