module.exports = {
    'parser': 'babel-eslint',
    'env': {
        'browser': true,
        'node': true,
        'mocha': true
    },
    'extends': [
        'prettier',
        'prettier/react',
        'airbnb',
        'plugin:react/recommended',
    ],
    'plugins': [
        'import',
        'prettier',
        'react',
    ],
    'rules': {
        'consistent-return': 0,
        'eol-last': 0,
        'no-use-before-define': 0,
        'global-require': 0,
        'no-unused-expressions': 0,
        'jsx-a11y/click-events-have-key-events': 0, // there are valid cases for this e.g. forms
        'jsx-a11y/interactive-supports-focus': 0, // there are valid cases for this e.g. forms
        'jsx-a11y/label-has-associated-control': 0, // rule seems buggy, doesn't understand some htmlFor cases
        'jsx-a11y/label-has-for': 0,
        'jsx-a11y/mouse-events-have-key-events': 0,
        'jsx-a11y/no-noninteractive-element-interactions': 0, // rule seems buggy, doesn't understand some htmlFor cases
        'max-len': 0,
        'react/jsx-one-expression-per-line': 0,
        'no-multi-assign': 0,
        'no-nested-ternary': 0,
        'no-param-reassign': 0, //Disabled to it not looking for global components
        'no-plusplus': 0,
        'no-restricted-globals': 'off',
        'no-return-assign': 0,
        'no-underscore-dangle': 0,
        'object-curly-newline': 0,
        'prefer-destructuring': 0,
        'quote-props': 0,
        'radix': 0,
        'indent': [
            "error", 4,
            {
                SwitchCase: 1,
                ignoredNodes: ['JSXElement', 'JSXElement > *', 'JSXAttribute', 'JSXIdentifier', 'JSXNamespacedName', 'JSXMemberExpression', 'JSXSpreadAttribute', 'JSXExpressionContainer', 'JSXOpeningElement', 'JSXClosingElement', 'JSXText', 'JSXEmptyExpression', 'JSXSpreadChild'],
            },
        ],
        'react/jsx-indent': ["error", 4],
        'react/jsx-indent-props': ["error", 2],
        'react/jsx-max-props-per-line': [1,
            {
                'maximum': 3
            }
        ],
        'react/destructuring-assignment': 0,
        'react/forbid-prop-types': 0,
        'react/jsx-filename-extension': 0,
        'react/jsx-no-undef': 0,
        'react/jsx-tag-spacing': 0, //Disabled to it not looking for global components
        'react/no-access-state-in-setstate': 0,
        'react/no-array-index-key': 0, // there are valid cases for this where a key can not be determined
        'react/no-direct-mutation-state': 0,
        'react/no-find-dom-node': 0,
        'react/no-multi-comp': 0,
        'react/no-string-refs': 0, // todo: Disable for now, need to update probably for react 17
        'react/no-unescaped-entities': 0, // there are valid cases for this where a key can not be determined
        'react/require-default-props': 0,
    },
    'globals': {
        '$': true,
        '_': true,
        '__DEV__': true,
        'AccountStore': true,
        'em': true,
        'Actions': true,
        'Any': true,
        'API': true,
        'AppActions': true,
        'AsyncStorage': true,
        'closeModal': true,
        'Constants': true,
        'Cookies': true,
        'describe': true,
        'Dispatcher': true,
        'ES6Component': true,
        'E2E': true,
        'Format': true,
        'FormGroup': true,
        'ga': true,
        'hot': true,
        'isMobile': true,
        'Link': true,
        'Loader': true,
        'mixpanel': true,
        'moment': true,
        'openConfirm': true,
        'openModal': true,
        'Permission': true,
        'Project': true,
        'propTypes': true,
        'Radio': true,
        'React': true,
        'ReactDOM': true,
        'Row': true,
        'routes': true,
        'SENTRY_RELEASE_VERSION': true,
        'pact': true,
        'testHelpers': true,
        'toast': true,
        'Utils': true,
        'window': true,
        "test": true,
        "fixture": true
    }
};
