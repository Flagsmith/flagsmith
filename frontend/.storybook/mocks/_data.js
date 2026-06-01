// Stub for common/data/base/_data — CommonJS file that breaks Storybook's ESM bundler.
// This is the Flux data layer used for API calls, not needed for component rendering.
module.exports = {
  get: () => Promise.resolve(),
  post: () => Promise.resolve(),
  put: () => Promise.resolve(),
  delete: () => Promise.resolve(),
}
