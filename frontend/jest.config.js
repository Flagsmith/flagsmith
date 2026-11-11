/** @type {import('jest').Config} */
module.exports = {
  clearMocks: true,
  collectCoverageFrom: [
    'common/**/*.{ts,tsx}',
    'web/**/*.{ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
  ],
  coverageDirectory: 'coverage',
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json'],
  moduleNameMapper: {
    // Components import their own SCSS; tests never need the styles.
    '\\.(css|scss)$': '<rootDir>/jest.styleMock.js',

    '^common/(.*)$': '<rootDir>/common/$1',

    '^components/(.*)$': '<rootDir>/web/components/$1',

    '^project/(.*)$': '<rootDir>/web/project/$1',

    // webpack resolves this one too; without it jest cannot follow the app.
    '^web/(.*)$': '<rootDir>/web/$1',
  },
  preset: 'ts-jest',
  roots: ['<rootDir>'],
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  // Logic tests run in node. Component tests opt into jsdom per file with a
  // `@jest-environment jsdom` docblock; see .claude/context/component-tests.md.
  testEnvironment: 'node',
  testMatch: ['**/__tests__/**/*.test.{ts,tsx}', '**/*.test.{ts,tsx}'],
  transform: {
    // Code-help snippet templates are ESM .js, so they need transforming too.
    // node_modules stays untransformed, hence the ignore pattern below.
    '^.+\\.(js|jsx|ts|tsx)$': [
      'ts-jest',
      {
        tsconfig: 'tsconfig.jest.json',
      },
    ],
  },
  transformIgnorePatterns: ['/node_modules/'],
  verbose: true,
}
