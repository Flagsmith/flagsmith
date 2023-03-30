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

