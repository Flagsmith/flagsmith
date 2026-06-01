// Define common loaders for different file types
// isDev is passed from the config to enable React Refresh in dev mode
module.exports = function getLoaders(isDev = false) {
  return [
    {
      exclude: /node_modules/,
      test: /\.(js|mjs|ts|tsx)$/,
      use: [
        {
          loader: 'builtin:swc-loader',
          options: {
            env: {
              targets: 'last 2 versions',
            },
            jsc: {
              externalHelpers: false,
              parser: {
                dynamicImport: true,
                syntax: 'typescript',
                tsx: true,
              },
              transform: {
                react: {
                  development: isDev,
                  refresh: isDev,
                  runtime: 'automatic',
                },
              },
            },
          },
        },
      ],
    },
    {
      test: /\.css$/,
      use: ['style-loader', 'css-loader'],
    },
    {
      test: /\.(md|txt)$/,
      type: 'asset/source',
    },
    {
      test: /\.html$/,
      type: 'asset/source',
    },
    {
      generator: {
        filename: '[hash][ext]',
      },
      test: /\.(otf|ttf|eot|png|jpg|jpeg|gif|svg|woff|woff2|ogv|mp4|webm)$/,
      type: 'asset/resource',
    },
  ]
}
