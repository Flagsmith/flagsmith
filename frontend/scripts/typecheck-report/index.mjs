#!/usr/bin/env node
// Counts TypeScript errors per file and compares two counts for the PR report.
//
//   node scripts/typecheck-report/index.mjs count <sha> <out.json>
//   node scripts/typecheck-report/index.mjs compare <base.json> <head.json> <current|stale|missing> <out.md>
//
// `compare` prints `comment` or `update` for the workflow to act on.
// Never fails on type errors: the report calls attention, it doesn't block.

import { existsSync, readFileSync, writeFileSync } from 'node:fs'
import { spawnSync } from 'node:child_process'
import { compareCounts, total } from './compare.ts'

const WITH_FILE = /^(.+?)\(\d+,\d+\): error TS\d+:/
const WITHOUT_FILE = /^error TS\d+:/

const count = (sha, out) => {
  const tsc = spawnSync(
    'npx',
    ['tsc', '--noEmit', '--pretty', 'false', '--incremental', 'false'],
    { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 },
  )
  // tsc exits 0 when clean and 1 or 2 when it reports errors; anything else
  // means it didn't run.
  if (tsc.error || ![0, 1, 2].includes(tsc.status)) {
    process.stderr.write(`${tsc.stdout}${tsc.stderr}`)
    process.exit(1)
  }
  const files = {}
  for (const line of tsc.stdout.split('\n')) {
    const file = line.match(WITH_FILE)?.[1] ?? (WITHOUT_FILE.test(line) && '(no file)')
    if (file) files[file] = (files[file] || 0) + 1
  }
  writeFileSync(out, `${JSON.stringify({ files, sha }, null, 2)}\n`)
  process.stdout.write(
    `${total(files)} errors in ${Object.keys(files).length} files\n`,
  )
}

const read = (path) =>
  existsSync(path) ? JSON.parse(readFileSync(path, 'utf8')) : null

const compare = (basePath, headPath, baseState, out) => {
  const report = compareCounts(read(basePath), read(headPath), baseState)
  writeFileSync(out, report.markdown)
  process.stdout.write(`${report.action}\n`)
}

const [mode, ...args] = process.argv.slice(2)
if (mode === 'count') count(...args)
else if (mode === 'compare') compare(...args)
else {
  process.stderr.write(
    'Usage: index.mjs count <sha> <out> | compare <base> <head> <state> <out>\n',
  )
  process.exit(1)
}
