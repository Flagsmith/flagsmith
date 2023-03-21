const path = require('path')

module.exports = {
  externals: {
    'jquery': 'jQuery',
  },
  resolve: {
    alias: {
      'common': path.resolve(__dirname, 'common'),
      'components': path.resolve(__dirname, 'web/components'),
      'project': path.resolve(__dirname, 'web/project'),
    },
    extensions: ['.tsx', '.ts', '.js'],
  },
}
