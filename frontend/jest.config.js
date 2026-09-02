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
    '^common/(.*)$': '<rootDir>/common/$1',
    '^components/(.*)$': '<rootDir>/web/components/$1',
    '^project/(.*)$': '<rootDir>/web/project/$1',
  },
  preset: 'ts-jest',
  roots: ['<rootDir>'],
  testEnvironment: 'node',
  testMatch: ['**/__tests__/**/*.test.ts', '**/*.test.ts'],
  // A Storybook build copies the source into storybook-static, so without
  // this jest runs a stale second copy of every test.
  testPathIgnorePatterns: ['/node_modules/', '/storybook-static/'],
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
