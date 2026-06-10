export default (serversideEnvironmentKey) => `
npm i @flagsmith/cli -g
export FLAGSMITH_ENVIRONMENT=${serversideEnvironmentKey}
flagsmith get -e document
`
