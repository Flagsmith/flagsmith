const path = require('path')
const webpack = require('webpack')

/** @type { import('storybook').StorybookConfig } */
const config = {
  stories: [
    '../documentation/**/*.mdx',
    '../documentation/**/*.stories.@(js|jsx|ts|tsx)',
  ],
  staticDirs: ['../web'],
  addons: [
    '@storybook/addon-webpack5-compiler-swc',
    '@storybook/addon-docs',
    '@storybook/addon-a11y',
  ],
  framework: {
    name: '@storybook/react-webpack5',
    options: {},
  },
  swc: () => ({
    jsc: {
      transform: {
        react: {
          runtime: 'automatic',
        },
      },
      parser: {
        syntax: 'typescript',
        tsx: true,
      },
    },
  }),
  webpackFinal: async (config) => {
    config.resolve = config.resolve || {}
    config.resolve.alias = {
      ...config.resolve.alias,
      common: path.resolve(__dirname, '../common'),
      components: path.resolve(__dirname, '../web/components'),
      project: path.resolve(__dirname, '../web/project'),
    }

    config.module = config.module || {}
    config.module.rules = config.module.rules || []
    config.module.rules.push({
      test: /\.scss$/,
      use: [
        'style-loader',
        { loader: 'css-loader', options: { importLoaders: 1 } },
        {
          loader: 'sass-loader',
          options: {
            sassOptions: {
              silenceDeprecations: ['slash-div'],
            },
          },
        },
      ],
    })

    config.plugins = config.plugins || []
    config.plugins.push(
      new webpack.DefinePlugin({
        E2E: false,
      }),
    )

    return config
  },
}
module.exports = config
