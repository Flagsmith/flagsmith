import { defineConfig, devices } from '@playwright/test'

require('dotenv').config()

const port = process.env.E2E_LOCAL ? 3000 : 8080
const baseURL = `http://localhost:${port}/`

export default defineConfig({
  expect: {
    timeout: 20000,
  },
  forbidOnly: !!process.env.CI,
  outputDir: 'reports/test-results',
  projects: [
    {
      name: 'api teardown',
      testMatch: /global\.setup\.ts/,
    },
    {
      dependencies: ['api teardown'],
      grep: /@oss/,
      name: 'oss',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      dependencies: ['api teardown'],
      grep: /@enterprise/,
      name: 'enterprise',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
  reporter: [['html'], ['list']],
  retries: process.env.CI ? 2 : 0,
  testDir: './e2e/tests',
  timeout: 30000,
  use: {
    baseURL,
    headless: process.env.E2E_DEV ? false : true,
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
    video: process.env.E2E_DEV
      ? 'off'
      : {
          mode: 'retain-on-failure',
          size: { height: 720, width: 1280 },
        },
  },
  webServer: process.env.E2E_LOCAL
    ? undefined
    : {
        command: 'node api/index.js',
        env: {
          NODE_ENV: 'production',
          PORT: String(port),
        },
        reuseExistingServer: false,
        timeout: 30000,
        url: baseURL,
      },
  workers: Number(process.env.E2E_CONCURRENCY) || 1,
})
