module.exports = ({ NPM_RN_CLIENT , NPM_CLIENT}) => `// npm
npm i ${NPM_CLIENT} ${NPM_RN_CLIENT} --save

// yarn
yarn add ${NPM_CLIENT} ${NPM_RN_CLIENT}

`;
