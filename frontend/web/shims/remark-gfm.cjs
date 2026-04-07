const remarkGfmModule = require('../../node_modules/remark-gfm/index.js')

const remarkGfm =
  remarkGfmModule && remarkGfmModule.default
    ? remarkGfmModule.default
    : remarkGfmModule

module.exports = remarkGfm
module.exports.default = remarkGfm
