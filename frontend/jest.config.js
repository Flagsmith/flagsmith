/** @type {import('jest').Config} */
module.exports = {
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
  transform: {
    '^.+\\.(js|jsx)$': 'babel-jest',
    '^.+\\.(ts|tsx)$': [
      'ts-jest',
      {
        tsconfig: 'tsconfig.json',
      },
    ],
  },
  verbose: true,
}
