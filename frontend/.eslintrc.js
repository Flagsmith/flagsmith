module.exports = {
    "env": {
        "es6": true,
        "browser": true,
        "node": true
    },
    "extends": [
        "eslint:recommended",
        "plugin:react/recommended",
        "plugin:@typescript-eslint/recommended",
        "plugin:prettier/recommended",
        "plugin:@dword-design/import-alias/recommended"
    ],
    "parser": "@typescript-eslint/parser",
    "parserOptions": {
        "ecmaVersion": 6,
        "sourceType": "module",
        "ecmaFeatures": {
            "legacyDecorators": true,
            "modules": true
        }
    },
    "plugins": [
        "react",
        "react-hooks",
        "@typescript-eslint"
    ],
    "rules": {
        "@dword-design/import-alias/prefer-alias": [
            "error",
            {
                "alias": {
                    "common": "./common/",
                }
            }
        ],
        "@typescript-eslint/no-non-null-assertion": "off",
        "@typescript-eslint/ban-types": "off",
        "@typescript-eslint/ban-ts-comment": "off",
        "typescript-eslint/no-empty-interface": "off",
        "@typescript-eslint/no-namespace": "off",
        "@typescript-eslint/no-empty-function": "off",
        "@typescript-eslint/no-explicit-any": "off",
        "@typescript-eslint/no-var-requires": "off",
        "default-case": "error",
        "dot-notation": "error",
        "guard-for-in": "error",
        "indent": [
            "error", 4,
            {
                SwitchCase: 1,
                ignoredNodes: ["JSXElement", "JSXElement > *", "JSXAttribute", "JSXIdentifier", "JSXNamespacedName", "JSXMemberExpression", "JSXSpreadAttribute", "JSXExpressionContainer", "JSXOpeningElement", "JSXClosingElement", "JSXText", "JSXEmptyExpression", "JSXSpreadChild"],
            },
        ],
        "no-caller": "error",
        "no-empty": "off",
        "no-empty-pattern": "off",
        "no-var": "error",
        "prefer-template": "error",
        "react-hooks/exhaustive-deps": "error",
        "react-hooks/rules-of-hooks": "error",
        "react/display-name": "off",
        "react/jsx-max-props-per-line": [1,
            {
                "maximum": 3,
            },
        ],
        "react/jsx-no-undef": [
            "error",
            {
                "allowGlobals": true
            }
        ],
        "react/jsx-uses-react": "off",
        "react/no-string-refs": "off",
        "react/prop-types": "off",
        "react/react-in-jsx-scope": "off",
        "object-curly-spacing": [
            "error",
            "always"
        ]
    },
    "settings": {
        "react": {
            "version": "detect"
        }
    },
    "globals": {
        "$": true,
        "$crisp": true,
        "API": true,
        "AccountStore": true,
        "Actions": true,
        "Any": true,
        "AppActions": true,
        "AsyncStorage": true,
        "Cookies": true,
        "Dispatcher": true,
        "E2E": true,
        "ES6Component": true,
        "FormGroup": true,
        "Link": true,
        "Loader": true,
        "OptionalBool": true,
        "OptionalFunc": true,
        "OptionalNode": true,
        "OptionalString": true,
        "Project": true,
        "Radio": true,
        "React": true,
        "ReactDOM": true,
        "RequiredFunc": true,
        "RequiredString": true,
        "Row": true,
        "SENTRY_RELEASE_VERSION": true,
        "Tooltip": true,
        "Utils": true,
        "_": true,
        "__DEV__": true,
        "closeModal": true,
        "delighted": true,
        "describe": true,
        "em": true,
        "flagsmith": true,
        "ga": true,
        "hot": true,
        "isMobile": true,
        "mixpanel": true,
        "moment": true,
        "openConfirm": true,
        "openModal": true,
        "pact": true,
        "projectOverrides": true,
        "propTypes": true,
        "routes": true,
        "testHelpers": true,
        "toast": true,
        "window": true,
        "zE": true,
    },
};
