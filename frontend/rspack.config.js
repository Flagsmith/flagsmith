const path = require('path')

// This is the base rspack configuration used by files in /rspack
module.exports = {
  externals: {},
  resolve: {
    alias: {
      'common': path.resolve(__dirname, './common'),
      'components': path.resolve(__dirname, './web/components'),
      'project': path.resolve(__dirname, './web/project'),
      'remark-gfm$': path.resolve(__dirname, './web/shims/remark-gfm.cjs'),
    },

    extensions: ['.tsx', '.ts', '.js'],

    fullySpecified: false,
    // Include project root so bare imports like 'web/routes' resolve
    modules: [path.resolve(__dirname), 'node_modules'],
  },
}
