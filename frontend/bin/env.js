/**
 * Created by kylejohnson on 02/08/2016.
 */
require('colors');
const fs = require('fs-extra');
const path = require('path');

const env = process.env.ENV || 'dev';
const src = path.resolve(__dirname, `../env/project_${env}.js`);
const target = path.resolve(__dirname, '../common/project.js');


console.log(`Using project_${env}.js`.green);

fs.copySync(src, target);
