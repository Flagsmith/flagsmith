module.exports = global.Project = {
    api: 'http://localhost:8000/api/v1/',
    flagsmithClientAPI: 'https://api.bullet-train.io/api/v1/',
    flagsmith: '8KzETdDeMY7xkqkSkY3Gsg',
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
};
