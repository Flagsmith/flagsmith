// @ts-check
import assert from 'node:assert/strict'
import path from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { renderOutput, renderTitle } from '../src/markdown.mjs'
import { readReport } from '../src/report.mjs'

// The fixture is a real Playwright JSON report, generated in a container-like
// root (/srv/app), with one changed, one new and one unchanged screenshot.
const fixtures = path.join(path.dirname(fileURLToPath(import.meta.url)), 'fixtures')
const report = path.join(fixtures, 'results.json')
const root = path.join(fixtures, 'root')

test('readReport__container_paths__rebases_attachments_onto_root_dir', () => {
  // Given / When
  const result = readReport(report, root)

  // Then
  assert.equal(result.total, 3)
  assert.equal(result.changed.length, 1)
  const [changed] = result.changed
  assert.equal(changed.title, 'flag-tests-pw-ts--features-list.png')
  assert.equal(changed.snapshot, 'flag-tests-pw-ts--features-list')
  assert.equal(changed.expected, path.join(root, 'snaps/flag-tests-pw-ts--features-list.png'))
  assert.match(changed.actual || '', /features-list-actual\.png$/)
  assert.match(changed.diff || '', /features-list-diff\.png$/)
})

test('readReport__failed_comparison__reads_pixel_difference', () => {
  // Given / When
  const [changed] = readReport(report, root).changed

  // Then
  assert.equal(changed.pixels, 760)
  assert.equal(changed.ratio, 0.32)
})

test('readReport__missing_baseline__lists_screenshot_as_added', () => {
  // Given / When
  const { added } = readReport(report, root)

  // Then
  assert.equal(added.length, 1)
  assert.equal(added[0].snapshot, 'project-test-pw-ts--new-project')
  assert.equal(added[0].expected, undefined)
  assert.match(added[0].actual || '', /new-project-actual\.png$/)
})

test('readReport__no_root_dir__leaves_unresolvable_paths_out', () => {
  // Given / When
  const [changed] = readReport(report).changed

  // Then
  assert.equal(changed.actual, undefined)
  assert.equal(changed.diff, undefined)
})

test('renderTitle__no_changes__reports_compared_count', () => {
  // Given / When
  const title = renderTitle({ added: [], changed: [], total: 26 })

  // Then
  assert.equal(title, 'No visual changes (26 compared)')
})

test('renderOutput__changes_with_images__renders_before_after_diff_table', () => {
  // Given
  const result = readReport(report, root)
  const urls = new Map([
    [result.changed[0], { actual: 'https://img/a.png', diff: 'https://img/d.png', expected: 'https://img/e.png' }],
  ])

  // When
  const output = renderOutput(result, urls, 'https://report')

  // Then
  assert.equal(output.title, '1 changed, 1 new of 3')
  assert.match(output.summary, /1 unchanged · 1 changed · 1 new/)
  assert.match(output.summary, /\[Full Playwright report\]\(https:\/\/report\)/)
  assert.match(output.text, /\| Before \| After \| Diff \|/)
  assert.match(output.text, /<img src="https:\/\/img\/d.png"/)
  assert.match(output.text, /760 px differ \(0.32\)/)
  assert.match(output.text, /\(no baseline\)/)
})

test('renderOutput__upload_failed__says_images_are_unavailable', () => {
  // Given
  const result = readReport(report, root)

  // When
  const { text } = renderOutput(result, new Map())

  // Then
  assert.match(text, /Images unavailable/)
  assert.doesNotMatch(text, /<img/)
})

test('renderOutput__html_in_titles__escapes_it', () => {
  // Given
  const comparison = { file: 'a.pw.ts', snapshot: 's', title: '<script>' }

  // When
  const { text } = renderOutput({ added: [], changed: [comparison], total: 1 }, new Map())

  // Then
  assert.match(text, /&lt;script&gt;/)
  assert.doesNotMatch(text, /<script>/)
})
