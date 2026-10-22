// Only added lines are checked, by reviewdog in CI, so existing styles don't
// fail a PR.
module.exports = {
  customSyntax: 'postcss-scss',
  overrides: [
    {
      // Where raw colour values and the dark theme are defined.
      files: [
        '.storybook/**',
        'documentation/**',
        'web/styles/_primitives.scss',
        'web/styles/_tokens.scss',
      ],
      rules: {
        'color-no-hex': null,
        'selector-disallowed-list': null,
      },
    },
  ],
  rules: {
    'color-no-hex': [true, { message: 'Use a colour token, not a hex literal.' }],
    'selector-disallowed-list': [
      [/\.dark(?![\w-])/],
      { message: 'Use a token whose value already changes in dark mode.' },
    ],
  },
}
