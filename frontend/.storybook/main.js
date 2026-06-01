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
  typescript: {
    reactDocgen: 'react-docgen-typescript',
    reactDocgenTypescriptOptions: {
      shouldExtractLiteralValuesFromEnum: true,
      shouldRemoveUndefinedFromOptional: true,
      propFilter: (prop) =>
        prop.parent ? !/node_modules/.test(prop.parent.fileName) : true,
    },
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
      // Stub CommonJS modules that break Storybook's ESM bundler.
      // code-help contains SDK snippets using module.exports — not needed for component rendering.
      'common/code-help': path.resolve(__dirname, 'mocks/code-help.js'),
      // Stub CommonJS data layer that breaks ESM bundler
      [path.resolve(__dirname, '../common/data/base/_data.js')]: path.resolve(__dirname, 'mocks/_data.js'),
      // Mock dompurify (CJS/ESM export mismatch)
      'dompurify': path.resolve(__dirname, 'mocks/dompurify.js'),
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

    // Stub modules that cause circular dependency crashes in Storybook.
    // common/utils/utils → account-store → constants creates a webpack
    // initialisation error. Ionic/stencil also triggers the same chain.
    config.resolve.alias = {
      ...config.resolve.alias,
      [path.resolve(__dirname, '../common/utils/utils')]: path.resolve(
        __dirname,
        'stubs/utils.js',
      ),
      '@stencil/core/internal/client': false,
      '@stencil/core': false,
      // Mock IonIcon so components that still use it (ClearFilters,
      // NavSubLink, BreadcrumbSeparator, etc.) can render in stories
      // without forcing each one to migrate to our Icon component.
      '@ionic/react': path.resolve(__dirname, 'mocks/ionic-react.js'),
      'ionicons/icons': path.resolve(__dirname, 'mocks/ionicons-icons.js'),
    }

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
