module.exports = {
  '*.{js,jsx}': ['suppress-exit-code eslint --fix'],
  '*.{ts,tsx}': [
    'suppress-exit-code eslint --fix',
    () => 'tsc --skipLibCheck --noEmit',
  ],
}
