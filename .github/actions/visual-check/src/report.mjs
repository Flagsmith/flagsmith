// @ts-check
import fs from 'node:fs'
import path from 'node:path'

/**
 * @typedef {{ name: string, contentType: string, path?: string }} Attachment
 * @typedef {{ status: string, retry: number, error?: { message?: string }, attachments: Attachment[] }} TestResult
 * @typedef {{ title: string, file: string, tests: { results: TestResult[] }[] }} Spec
 * @typedef {{ title: string, specs?: Spec[], suites?: Suite[] }} Suite
 * @typedef {{ config: { rootDir: string }, suites: Suite[] }} PlaywrightReport
 *
 * @typedef {{
 *   title: string,
 *   file: string,
 *   snapshot: string,
 *   expected?: string,
 *   actual?: string,
 *   diff?: string,
 *   pixels?: number,
 *   ratio?: number,
 * }} Comparison
 *
 * @typedef {{ total: number, changed: Comparison[], added: Comparison[] }} VisualResult
 */

const SNAPSHOT_ATTACHMENT = /^(.*)-(expected|actual|diff)\.png$/
const PIXELS = /([\d,]+) pixels \(ratio ([\d.]+)/
const ANSI = /\u001b\[[0-9;]*m/g

/**
 * Attachment paths are absolute to wherever Playwright ran. When it ran
 * somewhere else (e.g. a container), rebase them from the report's rootDir
 * onto the local rootDir.
 *
 * @param {string | undefined} file
 * @param {string} reportRoot
 * @param {string | undefined} localRoot
 */
export const resolveAttachment = (file, reportRoot, localRoot) => {
  if (!file) return undefined
  if (fs.existsSync(file)) return file
  if (!localRoot) return undefined
  const relative = path.relative(reportRoot, file)
  if (relative.startsWith('..')) return undefined
  const rebased = path.join(localRoot, relative)
  return fs.existsSync(rebased) ? rebased : undefined
}

/** @param {Suite[]} suites @returns {Spec[]} */
const flattenSpecs = (suites) =>
  suites.flatMap((suite) => [
    ...(suite.specs || []),
    ...flattenSpecs(suite.suites || []),
  ])

/**
 * @param {PlaywrightReport} report
 * @param {string} [localRoot]
 * @returns {VisualResult}
 */
export const parseReport = (report, localRoot) => {
  /** @type {VisualResult} */
  const result = { added: [], changed: [], total: 0 }

  for (const spec of flattenSpecs(report.suites)) {
    for (const test of spec.tests) {
      const last = test.results[test.results.length - 1]
      if (!last) continue
      result.total += 1
      if (last.status === 'passed') continue

      /** @type {Map<string, { comparison: Comparison, kinds: Set<string> }>} */
      const snapshots = new Map()
      for (const attachment of last.attachments) {
        const match = attachment.name.match(SNAPSHOT_ATTACHMENT)
        if (!match) continue
        const [, snapshot, kind] = match
        const entry = snapshots.get(snapshot) || {
          comparison: { file: spec.file, snapshot, title: spec.title },
          kinds: new Set(),
        }
        entry.kinds.add(kind)
        entry.comparison[/** @type {'expected' | 'actual' | 'diff'} */ (kind)] =
          resolveAttachment(attachment.path, report.config.rootDir, localRoot)
        snapshots.set(snapshot, entry)
      }

      const message = (last.error?.message || '').replace(ANSI, '')
      const pixels = message.match(PIXELS)
      for (const { comparison, kinds } of snapshots.values()) {
        if (kinds.has('diff')) {
          if (pixels) {
            comparison.pixels = Number(pixels[1].replace(/,/g, ''))
            comparison.ratio = Number(pixels[2])
          }
          result.changed.push(comparison)
        } else if (kinds.has('actual')) {
          // No baseline to diff against. Playwright's "expected" here is the
          // actual it just wrote, so it isn't a before image.
          delete comparison.expected
          result.added.push(comparison)
        }
      }
    }
  }

  return result
}

/**
 * @param {string} reportPath
 * @param {string} [localRoot]
 */
export const readReport = (reportPath, localRoot) =>
  parseReport(
    /** @type {PlaywrightReport} */ (
      JSON.parse(fs.readFileSync(reportPath, 'utf8'))
    ),
    localRoot,
  )
