import { defineConfig } from '@playwright/test'

/**
 * Minimal Playwright config for the visual regression comparison step.
 * No global setup, no web server, no browser — just PNG comparison.
 */
export default defineConfig({
  reporter: [
    [
      'html',
      {
        open: 'never',
        outputFolder:
          process.env.PLAYWRIGHT_HTML_REPORT ||
          './e2e/visual-regression-report',
      },
    ],
    ['list'],
  ],
  snapshotPathTemplate: './e2e/visual-regression-snapshots/{arg}{ext}',
  testDir: './e2e',
  testMatch: /.*_visual-regression-compare\.pw\.ts$/,
})
