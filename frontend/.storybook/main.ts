import type { StorybookConfig } from '@storybook/react-webpack5'
import path from 'path'

const config: StorybookConfig = {
  stories: ['../stories/**/*.mdx', '../stories/**/*.stories.@(js|jsx|ts|tsx)'],
  addons: [
    '@storybook/addon-webpack5-compiler-swc',
    '@storybook/addon-essentials',
    '@storybook/addon-a11y',
    '@storybook/addon-interactions',
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
    // Path aliases — match the project's webpack.config.js
    config.resolve = config.resolve || {}
    config.resolve.alias = {
      ...config.resolve.alias,
      common: path.resolve(__dirname, '../common'),
      components: path.resolve(__dirname, '../web/components'),
      project: path.resolve(__dirname, '../web/project'),
    }

    // SCSS support
    config.module = config.module || {}
    config.module.rules = config.module.rules || []
    config.module.rules.push({
      test: /\.scss$/,
      use: [
        'style-loader',
        { loader: 'css-loader', options: { importLoaders: 1 } },
        'sass-loader',
      ],
    })

    return config
  },
}
export default config
