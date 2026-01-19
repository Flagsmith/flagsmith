// Set up global Utils object for tests
// This makes Utils.accents and Utils.isInPast available globally as they are in the app
// eslint-disable-next-line @typescript-eslint/no-explicit-any
;(global as any).Utils = require('./common/utils/base/_utils')
