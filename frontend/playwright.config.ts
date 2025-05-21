import { defineConfig, devices } from '@playwright/test'

require('dotenv').config()

const baseURL = `http://localhost:${process.env.PORT || 8080}/`

export default defineConfig({
  expect: {
    timeout: 20000,
  },
  forbidOnly: !!process.env.CI,
  projects: [
    {
      name: 'api teardown',
      testMatch: /global\.setup\.ts/,
    },
    {
      name: 'run bundled app',
      testMatch: /serve-bundle\.setup\.ts/,
    },
    {
      name: 'teardown bundled app',
      testMatch: /global-teardown\.ts/,
    },
    {
      name: 'tests',
      testDir: './e2e/tests',
    },
    {
      dependencies: ['api teardown', 'run bundled app'],
      grep: /@oss/,
      name: 'oss',
      teardown: 'teardown bundled app',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      dependencies: ['api teardown', 'run bundled app'],
      grep: /@enterprise/,
      name: 'enterprise',
      teardown: 'teardown bundled app',
      use: { ...devices['Desktop Firefox'] },
    },
  ],
  reporter: [['html'], ['list']],
  retries: process.env.CI ? 2 : 0,
  testDir: './e2e/tests',
  timeout: 20000,
  use: {
    baseURL: process.env.E2E_LOCAL ? 'http://localhost:3000' : baseURL,
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
  workers: Number(process.env.E2E_CONCURRENCY) || 1,
})
