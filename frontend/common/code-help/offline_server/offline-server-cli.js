import _data from 'common/data/base/_data'
export default (serversideEnvironmentKey) => `
npm i flagsmith-cli -g
export FLAGSMITH_ENVIRONMENT=${serversideEnvironmentKey}
flagsmith get -e document
`
