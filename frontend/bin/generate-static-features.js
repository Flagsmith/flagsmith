const Project = require('../env/project_staging')
const process = require('child_process')
const flagsmithEnvironment = Project.flagsmith
const flagsmithAPI = Project.flagsmithClientAPI
if (flagsmithEnvironment && flagsmithAPI) {
  process.execSync(
    `FLAGSMITH_ENVIRONMENT=${flagsmithEnvironment} npx flagsmith get -p -a ${flagsmithAPI} -o ./env/flagsmith.json`,
  )
}
