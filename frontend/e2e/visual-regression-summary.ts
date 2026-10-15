import * as fs from 'fs'
import * as path from 'path'

type Attachment = { name: string }
type TestResult = {
  status: string
  error?: { message?: string }
  attachments: Attachment[]
}
type Spec = { title: string; tests: { results: TestResult[] }[] }
type Suite = { specs?: Spec[]; suites?: Suite[] }
export type VisualReport = { suites: Suite[] }

export type VisualChange = {
  title: string
  pixels?: number
  ratio?: number
  isNew: boolean
}

export type VisualSummary = { total: number; changes: VisualChange[] }

const REPORT_PATH = path.resolve(
  __dirname,
  'visual-regression-results',
  'report.json',
)
const PIXELS = /([\d,]+) pixels \(ratio ([\d.]+)/
const ANSI = /\u001b\[[0-9;]*m/g

const flattenSpecs = (suites: Suite[]): Spec[] =>
  suites.flatMap((suite) => [
    ...(suite.specs || []),
    ...flattenSpecs(suite.suites || []),
  ])

export const summariseReport = (report: VisualReport): VisualSummary => {
  const summary: VisualSummary = { changes: [], total: 0 }
  for (const spec of flattenSpecs(report.suites)) {
    for (const test of spec.tests) {
      const result = test.results[test.results.length - 1]
      if (!result) continue
      summary.total += 1
      if (result.status === 'passed') continue

      // Playwright only attaches a diff when there was a baseline to diff against.
      const isNew = !result.attachments.some((a) => a.name.endsWith('-diff.png'))
      const message = (result.error?.message || '').replace(ANSI, '')
      const pixels = message.match(PIXELS)
      summary.changes.push({
        isNew,
        pixels: pixels ? Number(pixels[1].replace(/,/g, '')) : undefined,
        ratio: pixels ? Number(pixels[2]) : undefined,
        title: spec.title,
      })
    }
  }
  return summary
}

const describeChange = ({ isNew, pixels, ratio }: VisualChange) => {
  if (isNew) return 'New, no baseline'
  if (pixels === undefined) return 'Changed'
  return `${pixels.toLocaleString('en-GB')} px differ (${ratio})`
}

export const renderSummary = ({ changes, total }: VisualSummary): string => {
  if (!changes.length) return `No visual changes in ${total} screenshots.`

  const changed = changes.filter((change) => !change.isNew).length
  const added = changes.length - changed
  const counts = [
    changed && `${changed} changed`,
    added && `${added} new`,
  ].filter(Boolean)
  return [
    `**${counts.join(', ')}** of ${total} screenshots`,
    '',
    '| Screenshot | Change |',
    '| --- | --- |',
    ...changes.map(
      (change) =>
        `| ${change.title.replace(/\|/g, '\\|')} | ${describeChange(change)} |`,
    ),
  ].join('\n')
}

if (require.main === module) {
  if (!fs.existsSync(REPORT_PATH)) {
    console.log('Screenshots were captured but the comparison did not run.')
  } else {
    const report = JSON.parse(fs.readFileSync(REPORT_PATH, 'utf8'))
    console.log(renderSummary(summariseReport(report)))
  }
}
