// Patterns we keep catching in review. Warnings only, on changed lines only
// (CI and pre-commit), so they never block a PR. For a real exception,
// disable the rule on that line and say why.
const colourMessage = 'Use a colour token, not a hex, rgb or hsl literal.'
const fetchMessage =
  'Add an RTK Query endpoint in common/services/ instead of fetch().'

const colourLiterals = [
  {
    message: colourMessage,
    selector:
      'Literal[value=/^\\s*(#([0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$|(rgba?|hsla?)\\()/]',
  },
  {
    message: colourMessage,
    selector:
      'TemplateElement[value.raw=/#([0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\\b|(rgba?|hsla?)\\(/]',
  },
]

// Legacy classes that have a DS component. Keep this list short: add a class
// only once its replacement exists, remove it once the last use migrates.
const legacyClasses = [
  { re: '(^|\\s)chip(--|\\s|$)', use: 'Chip' },
  { re: '(^|\\s)alert(\\s|$)', use: 'Banner' },
].flatMap(({ re, use }) => {
  const message = `Use the DS ${use} instead of the legacy class.`
  return [
    {
      message,
      selector: `JSXAttribute[name.name='className'] Literal[value=/${re}/]:not(CallExpression Literal)`,
    },
    {
      message,
      selector: `JSXAttribute[name.name='className'] TemplateElement[value.raw=/${re}/]`,
    },
    {
      message,
      selector: `CallExpression[callee.name=/^(cn|classNames|cx)$/] Literal[value=/${re}/]`,
    },
  ]
})

// A style object that only sets CSS custom properties is allowed.
const styleMessage =
  'Use a SCSS class with tokens. For a runtime value, set a CSS custom property.'
// `as const` only narrows, so it stays allowed.
const assertionMessage = 'Type the value instead of asserting its type.'
const otherPatterns = [
  ...legacyClasses,
  {
    message: assertionMessage,
    selector: "TSAsExpression:not([typeAnnotation.typeName.name='const'])",
  },
  {
    message: assertionMessage,
    selector: 'TSTypeAssertion',
  },
  {
    message: styleMessage,
    selector:
      "JSXAttribute[name.name='style'] > JSXExpressionContainer > :not(ObjectExpression)",
  },
  {
    message: styleMessage,
    selector:
      "JSXAttribute[name.name='style'] > JSXExpressionContainer > ObjectExpression > :not(Property[key.value=/^--/])",
  },
  {
    message: "Use BareButton instead of role='button'.",
    selector: "JSXAttribute[name.name='role'] Literal[value='button']",
  },
  {
    message: 'Give the element a role or accessible name instead of data-test.',
    selector: "JSXAttribute[name.name='data-test']",
  },
  {
    message: fetchMessage,
    selector:
      "CallExpression[callee.object.name=/^(window|globalThis|self)$/][callee.property.name='fetch']",
  },
]

module.exports = {
  'env': {
    'browser': true,
    'es6': true,
    'node': true,
  },
  'extends': [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:prettier/recommended',
    'plugin:@dword-design/import-alias/recommended',
    'plugin:storybook/recommended',
    // Lints only changed lines in CI and in the pre-commit hook (which sets
    // LINT_STAGED), so the pre-existing backlog doesn't fail a commit or PR.
    process.env.LINT_STAGED ? 'plugin:diff/staged' : 'plugin:diff/ci',
  ],
  'globals': {
    '$': true,
    'API': true,
    'AccountProvider': true,
    'AccountStore': true,
    'Actions': true,
    'Any': true,
    'AppActions': true,
    'AsyncStorage': true,
    'Button': true,
    'ButtonLink': true,
    'ButtonOutline': true,
    'ButtonProject': true,
    'Chargebee': true,
    'CodeHelp': true,
    'Column': true,
    'Cookies': true,
    'Dispatcher': true,
    'E2E': true,
    'ES6Component': true,
    'FB': true,
    'FeatureListProvider': true,
    'FeatureValue': true,
    'Flex': true,
    'FormGroup': true,
    'Headway': true,
    'Input': true,
    'InputGroup': true,
    'Link': true,
    'Loader': true,
    'OptionalArray': true,
    'OptionalBool': true,
    'OptionalFunc': true,
    'OptionalNode': true,
    'OptionalNumber': true,
    'OptionalObject': true,
    'OptionalString': true,
    'OrganisationProvider': true,
    'Paging': true,
    'Panel': true,
    'PanelSearch': true,
    'Project': true,
    'ProjectProvider': true,
    'Radio': true,
    'React': true,
    'ReactDOM': true,
    'RequiredElement': true,
    'RequiredFunc': true,
    'RequiredObject': true,
    'RequiredString': true,
    'Row': true,
    'SENTRY_RELEASE_VERSION': true,
    'Select': true,
    'Switch': true,
    'Tooltip': true,
    'Utils': true,
    '_': true,
    '__DEV__': true,
    'closeModal': true,
    'closeModal2': true,
    'delighted': true,
    'describe': true,
    'em': true,
    'flagsmith': true,
    'ga': true,
    'heap': true,
    'hljs': true,
    'hot': true,
    'isMobile': true,
    'moment': true,
    'oneOfType': true,
    'openConfirm': true,
    'openModal': true,
    'openModal2': true,
    'pact': true,
    'projectOverrides': true,
    'propTypes': true,
    'routes': true,
    'testHelpers': true,
    'toast': true,
    'window': true,
    'zE': true,
  },
  'ignorePatterns': ['server/index.js', 'next.config.js', 'babel.config.js'],
  'overrides': [
    {
      // Where raw colour values are defined or are brand colours.
      'files': [
        '.storybook/**',
        'common/constants.ts',
        'common/theme/**',
        'common/utils/paletteColour.ts',
        'documentation/**',
        'web/components/icons/**',
      ],
      'rules': {
        'no-restricted-syntax': ['warn', ...otherPatterns],
      },
    },
    {
      // The legacy request layer RTK Query is built on.
      'files': ['common/data/base/**'],
      'rules': {
        'no-restricted-globals': 'off',
      },
    },
  ],
  'parser': '@typescript-eslint/parser',
  'parserOptions': {
    'ecmaFeatures': {
      'legacyDecorators': true,
      'modules': true,
    },
    'ecmaVersion': 6,
    'sourceType': 'module',
  },
  'plugins': [
    'react',
    'react-hooks',
    'sort-keys-fix',
    'sort-destructure-keys',
    '@typescript-eslint',
    'unused-imports',
  ],
  'rules': {
    '@dword-design/import-alias/prefer-alias': [
      'error',
      {
        'alias': {
          'common': './common/',
          'components': './web/components/',
          'project': './web/project/',
        },
      },
    ],
    '@typescript-eslint/ban-ts-comment': 'off',
    '@typescript-eslint/ban-types': 'off',
    '@typescript-eslint/no-empty-function': 'off',
    '@typescript-eslint/no-explicit-any': 'off',
    '@typescript-eslint/no-namespace': 'off',
    '@typescript-eslint/no-non-null-assertion': 'warn',
    '@typescript-eslint/no-unused-vars': 'off',
    '@typescript-eslint/no-var-requires': 'off',
    'default-case': 'error',
    'dot-notation': 'error',
    'eqeqeq': 'warn',
    'guard-for-in': 'error',
    'no-caller': 'error',
    'no-console': 'warn',
    'no-debugger': 'warn',
    'no-empty': 'off',
    'no-empty-pattern': 'off',
    'no-nested-ternary': 'error',
    'no-restricted-globals': [
      'warn',
      {
        message: fetchMessage,
        name: 'fetch',
      },
    ],
    'no-restricted-imports': [
      'warn',
      {
        patterns: [
          {
            group: ['**/ErrorMessage', '**/InfoMessage', '**/WarningMessage'],
            message: 'Use the DS Banner (components/base/Banner) instead.',
          },
          {
            group: ['@ionic/react', 'ionicons', 'ionicons/*'],
            message: 'Use components/icons/Icon, our own SVG icons.',
          },
        ],
      },
    ],
    'no-restricted-syntax': ['warn', ...colourLiterals, ...otherPatterns],
    'no-unused-vars': 'off',
    'no-var': 'error',
    'object-curly-spacing': ['error', 'always'],
    'prefer-template': 'error',
    'react-hooks/exhaustive-deps': 'error',
    'react-hooks/rules-of-hooks': 'error',
    'react/display-name': 'off',
    'react/jsx-no-undef': [
      'error',
      {
        'allowGlobals': true,
      },
    ],
    'react/jsx-uses-react': 'off',
    'react/no-direct-mutation-state': 'off',
    'react/no-find-dom-node': 'off',
    'react/no-string-refs': 'off',
    'react/no-unescaped-entities': 'off',
    'react/prop-types': 'off',
    'react/react-in-jsx-scope': 'off',
    'sort-destructure-keys/sort-destructure-keys': 'warn',
    'sort-keys-fix/sort-keys-fix': 'warn',
    'typescript-eslint/no-empty-interface': 'off',
    'unused-imports/no-unused-imports': 'error',
    'unused-imports/no-unused-vars': [
      'warn',
      {
        'argsIgnorePattern': '^_',
        'varsIgnorePattern': '^_',
      },
    ],
  },
  'settings': {
    'react': {
      'version': 'detect',
    },
  },
}
