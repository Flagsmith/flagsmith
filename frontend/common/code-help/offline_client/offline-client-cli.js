module.exports = (envId) => `
npm i flagsmith-cli -g
export FLAGSMITH_ENVIRONMENT=${envId}
flagsmith get
`
