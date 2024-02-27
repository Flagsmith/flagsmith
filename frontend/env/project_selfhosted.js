const globalThis = typeof window === 'undefined' ? global : window
module.exports = global.Project = {
  env: 'selfhosted',

  // Self Hosted Defaults environment
  flagsmith: 'MXSepNNQEacBBzxAU7RagJ',
  flagsmithClientAPI: 'https://edge.api.flagsmith.com/api/v1/',

  // This is used for Sentry tracking
  maintenance: false,
  useSecureCookies: true,
  ...(globalThis.projectOverrides || {}),
}
