import Utils from '../../utils/utils';

module.exports = ({ NPM_CLIENT, URL_CLIENT }) => `// npm
npm i ${NPM_CLIENT} --save

// yarn
yarn add ${NPM_CLIENT}

// Or script tag
${Utils.escapeHtml(`<script src="${URL_CLIENT}"></script>`)}
`;
