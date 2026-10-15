#!/usr/bin/env node
// Counts TypeScript errors per file and compares two counts for the PR report.
//
//   node scripts/typecheck-report.mjs count <out.json>
//   node scripts/typecheck-report.mjs compare <base.json> <head.json> <out.md>
//
// `compare` prints the change in the total, or `none` when there is no base.
// Never fails on type errors: the report calls attention, it doesn't block.

import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import { spawnSync } from 'node:child_process'

const ERROR_LINE = /^(.+?)\(\d+,\d+\): error TS\d+:/

const count = (out) => {
  const tsc = spawnSync(
    'npx',
    ['tsc', '--noEmit', '--pretty', 'false', '--incremental', 'false'],
    {
      encoding: 'utf8',
      maxBuffer: 64 * 1024 * 1024,
    },
  )
  const files = {}
  for (const line of tsc.stdout.split('\n')) {
    const match = line.match(ERROR_LINE)
    if (match) files[match[1]] = (files[match[1]] || 0) + 1
  }
  // tsc exits 1 when it finds errors; anything else means it didn't run.
  if (tsc.status !== 0 && !Object.keys(files).length) {
    process.stderr.write(tsc.stdout + tsc.stderr)
    process.exit(1)
  }
  writeFileSync(out, `${JSON.stringify(files, null, 2)}\n`)
  process.stdout.write(
    `${total(files)} errors in ${Object.keys(files).length} files\n`,
  )
}

const total = (files) => Object.values(files).reduce((sum, n) => sum + n, 0)

const signed = (n) => (n > 0 ? `+${n}` : `${n}`)

const compare = (basePath, headPath, out) => {
  const head = JSON.parse(readFileSync(headPath, 'utf8'))
  if (!existsSync(basePath)) {
    writeFileSync(
      out,
      `## TypeScript errors\n${total(
        head,
      )} errors. No count from main to compare with yet.\n`,
    )
    process.stdout.write('none\n')
    return
  }
  const base = JSON.parse(readFileSync(basePath, 'utf8'))
  const diff = total(head) - total(base)
  const changed = [...new Set([...Object.keys(base), ...Object.keys(head)])]
    .map((file) => ({ delta: (head[file] || 0) - (base[file] || 0), file }))
    .filter(({ delta }) => delta !== 0)
    .sort((a, b) => b.delta - a.delta || a.file.localeCompare(b.file))

  const icon = { '-1': '🟢', 0: '⚪️', 1: '🔴' }[Math.sign(diff)]
  const lines = [
    '## TypeScript errors',
    `${icon} ${total(base)} → ${total(head)} (${signed(diff)})`,
  ]
  if (changed.length) {
    lines.push(
      '',
      '| File | Change |',
      '| --- | --- |',
      ...changed.map(({ delta, file }) => `| \`${file}\` | ${signed(delta)} |`),
    )
  }
  writeFileSync(out, `${lines.join('\n')}\n`)
  process.stdout.write(`${diff}\n`)
}

const [mode, ...args] = process.argv.slice(2)
if (mode === 'count') count(...args)
else if (mode === 'compare') compare(...args)
else {
  process.stderr.write(
    'Usage: typecheck-report.mjs count <out> | compare <base> <head> <out>\n',
  )
  process.exit(1)
}
