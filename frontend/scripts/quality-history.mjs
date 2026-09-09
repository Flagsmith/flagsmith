#!/usr/bin/env node
// Builds the quarter-by-quarter view of the migration metrics by counting the
// last commit of each quarter. Everything comes from `git grep`, so no quarter
// needs checking out or installing.
//
//   node scripts/quality-history.mjs           # prints a table
//   node scripts/quality-history.mjs --write   # updates scripts/quality-history.json

import { execFileSync } from 'node:child_process'
import { writeFileSync } from 'node:fs'

// Quarter starts, from the first quarter we want to report on.
const QUARTER_STARTS = [
  '2025-10-01',
  '2026-01-01',
  '2026-04-01',
  '2026-07-01',
  '2026-10-01',
]

const root = execFileSync('git', ['rev-parse', '--show-toplevel'], {
  encoding: 'utf8',
}).trim()

const git = (args) =>
  execFileSync('git', args, { cwd: root, encoding: 'utf8' }).trim()

const label = (start) => {
  const [year, month] = start.split('-').map(Number)
  return `${year}-Q${Math.floor((month - 1) / 3) + 1}`
}

// A quarter is reported at its last commit, so the row is "where we finished".
// The quarter in progress is reported at HEAD instead.
const snapshots = []
for (const [i, start] of QUARTER_STARTS.entries()) {
  const next = QUARTER_STARTS[i + 1]
  const inProgress = !next || new Date(next) > new Date()
  const sha = inProgress
    ? git(['rev-parse', 'HEAD'])
    : git(['rev-list', '-1', `--before=${next}`, 'HEAD'])
  if (!sha) continue
  if (new Date(git(['log', '-1', '--format=%cs', sha])) < new Date(start))
    continue
  snapshots.push({ inProgress, quarter: label(start), sha })
  if (inProgress) break
}

const rows = snapshots.map(({ inProgress, quarter, sha }) => {
  const report = JSON.parse(
    execFileSync('node', ['scripts/quality-metrics.mjs', '--ref', sha], {
      cwd: `${root}/frontend`,
      encoding: 'utf8',
    }),
  )
  return { ...report, inProgress, quarter }
})

const history = {
  generatedAt: new Date().toISOString().slice(0, 10),
  quarters: rows,
}

if (process.argv.includes('--write')) {
  writeFileSync(
    `${root}/frontend/scripts/quality-history.json`,
    `${JSON.stringify(history, null, 2)}\n`,
  )
}

const names = Object.keys(rows[0]?.metrics ?? {})
const width = Math.max(...names.map((n) => n.length))
const head = rows.map((r) => (r.inProgress ? `${r.quarter}*` : r.quarter))
process.stdout.write(
  `${'metric'.padEnd(width)}  ${head.map((h) => h.padStart(9)).join('')}\n`,
)
for (const name of names) {
  const cells = rows
    .map((r) => String(r.metrics[name] ?? '').padStart(9))
    .join('')
  process.stdout.write(`${name.padEnd(width)}  ${cells}\n`)
}
process.stdout.write('\n* quarter in progress, counted at HEAD\n')
