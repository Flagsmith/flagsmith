const path = require('path')
const fs = require('fs')
const rspack = require('@rspack/core')

class CopyStaticPlugin {
  constructor(src, dest) {
    this.src = src
    this.dest = dest
  }

  apply(compiler) {
    compiler.hooks.afterEmit.tap('CopyStaticPlugin', () => {
      try {
        fs.cpSync(this.src, this.dest, { recursive: true })
      } catch (error) {
        compiler.errors.push(
          new Error(
            `CopyStaticPlugin: Failed to copy ${this.src} to ${this.dest}: ${error.message}`,
          ),
        )
      }
    })
  }
}

const plugins = [
  // Fixes warning in moment-with-locales.min.js
  // Module not found: Error: Can't resolve './locale' in ...
  new rspack.IgnorePlugin({
    contextRegExp: /moment$/,
    resourceRegExp: /^\.\/locale$/,
  }),
  // Copy static content
  new CopyStaticPlugin(
    path.join(__dirname, '../web/static'),
    path.join(__dirname, '../public/static'),
  ),
]

plugins.CopyStaticPlugin = CopyStaticPlugin

module.exports = plugins
