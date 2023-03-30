/**
 * Created by kylejohnson on 02/08/2016.
 */
require('colors')
const fs1 = require('fs')
const fs = require('fs-extra')
const path = require('path')
const { execSync } = require('child_process')
const env = process.env.ENV || 'dev'
const src = path.resolve(__dirname, `../env/project_${env}.js`)
const target = path.resolve(__dirname, '../common/project.js')
fs.copySync(src, target)
const Project = require('../env/project_staging')
const flagsmithEnvironment =
  process.env.FLAGSMITH_ON_FLAGSMITH_API_KEY || Project.flagsmith
const flagsmithAPI =
  process.env.FLAGSMITH_ON_FLAGSMITH_API_URL || Project.flagsmithClientAPI
if (flagsmithEnvironment && flagsmithAPI) {
  execSync(
    `FLAGSMITH_ENVIRONMENT=${flagsmithEnvironment} npx flagsmith get -a ${flagsmithAPI} -o ./env/flagsmith.json`,
  )
}

// eslint-disable-next-line
console.log(`Using project_${env}.js`.green);

