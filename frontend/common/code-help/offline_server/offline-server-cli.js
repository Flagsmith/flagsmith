import _data from 'common/data/base/_data'
module.exports = (serversideEnvironmentKey) => `
npm i flagsmith-cli -g
export FLAGSMITH_ENVIRONMENT=${serversideEnvironmentKey}
flagsmith get -e document
`
