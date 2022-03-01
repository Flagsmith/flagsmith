module.exports = global.Project = {
    api: 'https://api-staging.flagsmith.com/api/v1/',
    flagsmithClientAPI: 'https://api.flagsmith.com/api/v1/',
    flagsmith: 'ENktaJnfLVbLifybz34JmX', // This is our Bullet Train API key - Bullet Train runs on Bullet Train!
    env: 'staging', // This is used for Sentry tracking
    maintenance: false, // trigger maintenance mode
    demoAccount: {
        email: 'kyle+bullet-train@solidstategroup.com',
        password: 'demo_account',
    },
    chargebee: {
        site: 'flagsmith-test',
    },
};
