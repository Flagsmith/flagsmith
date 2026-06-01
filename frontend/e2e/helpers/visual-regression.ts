import { expect, Page, TestInfo } from '@playwright/test'
import * as fs from 'fs'
import * as path from 'path'

/**
 * CSS injected before every visual snapshot to hide dynamic content
 * that changes between runs. Playwright's toHaveScreenshot() already
 * handles animations (animations: 'disabled') and caret (caret: 'hide'),
 * so we only target app-specific volatile elements here.
 */
const STABILISING_CSS = `
  /* Hide environment select (contains dynamic API key) */
  #environment-select {
    visibility: hidden !important;
  }

  /* Hide timestamps and relative dates */
  .ago,
  time,
  [data-test*="timestamp"],
  [data-test*="ago"],
  .text-muted:has(> .ago),
  .relative-date {
    visibility: hidden !important;
  }

  /* Hide loading spinners */
  .spinner,
  .loader,
  [class*="spinner"],
  [class*="loader"] {
    display: none !important;
  }

  /* Hide any live chat / support widgets */
  .intercom-launcher,
  #intercom-container,
  .drift-widget,
  [class*="chatbot"],
  iframe[title*="chat"],
  iframe[title*="Chat"] {
    display: none !important;
  }

  /* Stabilise scrollbars across platforms */
  ::-webkit-scrollbar {
    display: none !important;
  }
  * {
    scrollbar-width: none !important;
  }
`

/** Directory where screenshots are captured during E2E runs */
const SCREENSHOTS_DIR = path.resolve(process.cwd(), 'e2e', 'visual-regression-screenshots')

/** Directory where baselines live (downloaded from main in CI) */
const BASELINES_DIR = path.resolve(process.cwd(), 'e2e', 'visual-regression-snapshots')

/**
 * Whether visual regression snapshots are enabled for this run.
 */
export function isVisualRegressionEnabled(): boolean {
  return process.env.VISUAL_REGRESSION === '1'
}

/**
 * Wait for the page to settle before taking a screenshot.
 */
async function preparePage(page: Page): Promise<void> {
  await page.addStyleTag({ content: STABILISING_CSS })

  // Wait for images to finish loading
  await page
    .evaluate(() => {
      return Promise.all(
        Array.from(document.images)
          .filter((img) => !img.complete)
          .map(
            (img) =>
              new Promise((resolve) => {
                img.addEventListener('load', resolve)
                img.addEventListener('error', resolve)
                setTimeout(resolve, 5000)
              }),
          ),
      )
    })
    .catch(() => {})

  // Double rAF to ensure paint is complete
  await page.evaluate(() => {
    return new Promise((resolve) => {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          resolve(undefined)
        })
      })
    })
  })

  // Small settle time for any final layout shifts
  await page.waitForTimeout(500)
}

/**
 * Take a screenshot during E2E tests and save it to the screenshots directory.
 *
 * This ONLY captures the screenshot — it does NOT compare against baselines.
 * Comparison happens as a separate step after all E2E retries have completed,
 * via `npx tsx e2e/compare-visual-regression.ts`.
 *
 * @param page     Playwright page
 * @param name     Descriptive snapshot name, e.g. "features-list"
 * @param testInfo Playwright testInfo for resolving the test file name
 */
export async function visualSnapshot(
  page: Page,
  name: string,
  testInfo: TestInfo,
): Promise<void> {
  if (!isVisualRegressionEnabled()) return

  await preparePage(page)

  // Save with the sanitised name Playwright's toMatchSnapshot expects:
  // {testFileName}--{name} with dots replaced by dashes
  const testFileName = path.basename(testInfo.file)
  const sanitisedName = `${testFileName}--${name}`.replace(/\./g, '-')
  fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true })

  const screenshotPath = path.join(SCREENSHOTS_DIR, `${sanitisedName}.png`)
  await page.screenshot({
    path: screenshotPath,
    fullPage: true,
    animations: 'disabled',
    caret: 'hide',
    scale: 'css',
  })
}
