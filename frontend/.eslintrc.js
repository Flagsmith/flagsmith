// Patterns we keep catching in review. CI and pre-commit lint changed lines
// only, so existing uses don't fail a PR. For a real exception, disable the
// rule on that line and say why.
const colourLiterals = [
  {
    message: 'Use a colour token, not a hex, rgb or hsl literal.',
    selector:
      'Literal[value=/^\\s*(#([0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$|(rgba?|hsla?)\\()/]',
  },
  {
    message: 'Use a colour token, not a hex, rgb or hsl literal.',
    selector:
      'TemplateElement[value.raw=/#[0-9a-fA-F]{6}\\b|(rgba?|hsla?)\\(/]',
  },
]

const jsxPatterns = [
  {
    message:
      'Use a SCSS class with tokens. For a runtime value, set a CSS custom property.',
    selector: "JSXAttribute[name.name='style']",
  },
  {
    message: 'Give the element a role or accessible name instead of data-test.',
    selector: "JSXAttribute[name.name='data-test']",
  },
  {
    message: 'Use IconButton.',
    selector:
      "JSXAttribute[name.name='className'] Literal[value=/(^|\\s)btn-with-icon(\\s|$)/]",
  },
  {
    message: 'Use IconButton.',
    selector:
      "JSXOpeningElement[name.name='Button'] > JSXAttribute[name.name='theme'][value.value='icon']",
  },
  {
    message: 'Pass icons as children.',
    selector: 'JSXAttribute[name.name=/^icon(Left|Right)$/]',
  },
  {
    message: "Use BareButton instead of role='button'.",
    selector: "JSXAttribute[name.name='role'][value.value='button']",
  },
  {
    message:
      'Use the Bootstrap 5 name (fw-*, ms-*, me-*, ps-*, pe-*, float-start, text-end).',
    selector:
      "JSXAttribute[name.name='className'] Literal[value=/(^|\\s)(font-weight-[a-z]+|float-(left|right)|text-(left|right)|[mp][lr]-([0-9]|auto))(\\s|$)/]",
  },
]

const e2eSelectors = [
  {
    message: 'Use getByRole or getByLabel.',
    selector: "CallExpression[callee.name='byId']",
  },
  {
    message: 'Use getByRole or getByLabel.',
    selector:
      "CallExpression[callee.property.name='locator'] :matches(Literal[value=/data-test/], TemplateElement[value.raw=/data-test/])",
  },
]

const iconLibraries = {
  paths: [
    '@heroicons/react',
    '@mui/icons-material',
    '@phosphor-icons/react',
    'lucide-react',
    'react-icons',
  ].map((name) => ({
    message: 'Add the SVG to the project and render it through Icon.',
    name,
  })),
}
// A warning, not an error: some data is only in the stores until the RTK
// migration, and touching a line that already reads one shouldn't fail CI.
const fluxStores = {
  group: ['common/stores/*', '**/stores/*-store'],
  message: 'Read data through RTK Query services, not Flux stores.',
}
const fetchGlobal = {
  message: 'Add an RTK Query endpoint in common/services/ instead of fetch().',
  name: 'fetch',
}

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
        'documentation/**',
        'web/components/icons/**',
      ],
      'rules': {
        'no-restricted-syntax': ['error', ...jsxPatterns],
      },
    },
    {
      'files': ['common/stores/**', 'common/providers/**'],
      'rules': {
        '@typescript-eslint/no-restricted-imports': 'off',
      },
    },
    {
      // The legacy request layer RTK Query is built on.
      'files': ['common/data/base/**'],
      'rules': {
        'no-restricted-globals': 'off',
      },
    },
    {
      // E2E was outside lint until these rules, so it keeps its own formatting
      // and relative imports.
      'files': ['e2e/**'],
      'rules': {
        '@dword-design/import-alias/prefer-alias': 'off',
        'no-restricted-globals': 'off',
        'no-restricted-syntax': ['error', ...colourLiterals, ...e2eSelectors],
        'prettier/prettier': 'off',
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
    '@typescript-eslint/consistent-type-assertions': [
      'error',
      { 'assertionStyle': 'never' },
    ],
    '@typescript-eslint/no-empty-function': 'off',
    '@typescript-eslint/no-explicit-any': 'off',
    '@typescript-eslint/no-namespace': 'off',
    '@typescript-eslint/no-non-null-assertion': 'error',
    '@typescript-eslint/no-restricted-imports': [
      'warn',
      { 'patterns': [fluxStores] },
    ],
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
    'no-restricted-globals': ['error', fetchGlobal],
    'no-restricted-imports': ['error', iconLibraries],
    'no-restricted-syntax': ['error', ...colourLiterals, ...jsxPatterns],
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
    'react/no-danger': 'error',
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
