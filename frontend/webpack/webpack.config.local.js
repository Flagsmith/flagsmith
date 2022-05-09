// webpack.config.dev.js
const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const path = require('path');

const whitelabel = typeof process.env.WHITELABEL === 'undefined' ? false : process.env.WHITELABEL;
const styles = whitelabel ? path.join(__dirname, `../web/styles/whitelabel/${process.env.WHITELABEL}`) : path.join(__dirname, '../web/styles');
module.exports = {
    devtool: 'eval-source-map',
    mode: 'development',
    stats: 'errors-only',
    entry: [
        'webpack-hot-middleware/client?reload=false',
        './web/main.js',
    ],
    devServer: {
        outputPath: __dirname,
    },
    output: {
        path: path.join(__dirname, '../public'),
        filename: '[name].js',
        publicPath: '/',
        devtoolModuleFilenameTemplate: 'file://[absolute-resource-path]',
    },
    externals: {
        // require('jquery') is external and available
        //  on the global var jQuery
        'jquery': 'jQuery',
    },
    resolve: {
        alias: {
            styles,
        },
    },
    plugins: require('./plugins').concat([
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
    ]).concat(require('./pages').map((page) => {
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
                            sourceMap: true,
                            convertToAbsoluteUrls: false,
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
