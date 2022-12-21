module.exports = global.Project = {
    api: 'https://api.flagsmith.com/api/v1/',
    flagsmithClientAPI: 'https://api.flagsmith.com/api/v1/',
    flagsmithClientEdgeAPI: 'https://edge.api.flagsmith.com/api/v1/',
    flagsmith: '4vfqhypYjcPoGGu8ByrBaj', // This is our Bullet Train API key - Bullet Train runs on Bullet Train!
    env: 'prod', // This is used for Sentry tracking
    maintenance: false, // trigger maintenance mode
    cookieDomain: '.flagsmith.com',
    excludeAnalytics: 'nightwatch@solidstategroup.com',
    demoAccount: {
        email: 'kyle+bullet-train@solidstategroup.com',
        password: 'demo_account',
    },
    chargebee: {
        site: 'flagsmith',
    },
};
