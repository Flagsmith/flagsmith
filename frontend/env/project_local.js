const globalThis = typeof window === "undefined"? global : window;
module.exports = global.Project = {
    api: 'http://localhost:8000/api/v1/',
    flagsmithClientAPI: 'https://api.flagsmith.com/api/v1/',
    flagsmithClientEdgeAPI: 'https://edge.api.flagsmith.com/api/v1/',
    flagsmith: 'ENktaJnfLVbLifybz34JmX',
    debug: false,
    env: 'dev', // This is used for Sentry tracking
    maintenance: false, // trigger maintenance mode
    demoAccount: {
        email: 'kyle+bullet-train@solidstategroup.com',
        password: 'demo_account',
    },
    chargebee: {
        site: 'flagsmith-test',
    },
    ...(globalThis.projectOverrides||{})
};
