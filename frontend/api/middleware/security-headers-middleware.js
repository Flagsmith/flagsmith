const helmet = require('helmet')

module.exports = [
  helmet.contentSecurityPolicy({
    directives: {
      defaultSrc: helmet.contentSecurityPolicy.dangerouslyDisableDefaultSrc,
      frameAncestors: ["'none'"],
    },
    useDefaults: false,
  }),
  helmet.xFrameOptions({ action: 'deny' }),
  helmet.xContentTypeOptions(),
  helmet.referrerPolicy({ policy: 'strict-origin-when-cross-origin' }),
  helmet.xPoweredBy(),
]
