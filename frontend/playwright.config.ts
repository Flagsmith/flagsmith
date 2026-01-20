import { defineConfig, devices } from '@playwright/test'

/**
 * Read environment variables from file.
 * https://github.com/motdotla/dotenv
 */
require('dotenv').config()

/**
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Global setup and teardown */
  globalSetup: require.resolve('./e2e/global-setup.playwright.ts'),
  globalTeardown: require.resolve('./e2e/global-teardown.playwright.ts'),
  /* Output directory for test results */
  outputDir: './e2e/test-results',
  /* Configure projects for major browsers */
  projects: [
    {
      name: 'firefox',
      use: {
        ...devices['Desktop Firefox'],
        headless: !process.env.E2E_DEV,
        // Launch options for Firefox
        launchOptions: {
          // Try to use system Firefox if PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD was set
          executablePath: process.env.PLAYWRIGHT_FIREFOX_PATH || undefined,
          firefoxUserPrefs: {
            // Disable auto-updates to prevent version conflicts
            'app.update.auto': false,
            'app.update.enabled': false,
          },
        },
      },
    },
  ],
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [
    ['html', { open: 'never', outputFolder: './e2e/playwright-report' }],
    ['list', { printSteps: false }], // Only shows test names with pass/fail status
  ],
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  testDir: './e2e',
  testMatch: /.*\.pw\.ts$/,
  /* Test timeout */
  timeout: 120000,
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Action timeout */
    actionTimeout: 20000,
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: `http://localhost:${process.env.PORT || 8080}`,
    /* Navigation timeout */
    navigationTimeout: 20000,
    /* Screenshot on failure */
    screenshot: 'only-on-failure',
    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry',
    /* Video on failure */
    video: process.env.E2E_DEV ? 'retain-on-failure' : 'on-first-retry',
  },
  /* Run your local dev server before starting the tests */
  webServer: process.env.E2E_LOCAL
    ? undefined
    : {
        command: 'npm run start',
        port: 8080,
        reuseExistingServer: !process.env.CI,
        timeout: 120 * 1000,
      },
  /* Opt out of parallel tests on CI. */
  workers: process.env.E2E_CONCURRENCY
    ? parseInt(process.env.E2E_CONCURRENCY)
    : 3,
})
