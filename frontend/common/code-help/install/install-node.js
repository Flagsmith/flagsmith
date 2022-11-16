module.exports = ({ NPM_NODE_CLIENT }) => `// npm
npm i ${NPM_NODE_CLIENT} --save

// yarn
yarn add ${NPM_NODE_CLIENT}
`;
