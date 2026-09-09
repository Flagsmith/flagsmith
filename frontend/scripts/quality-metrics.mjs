#!/usr/bin/env node
// Counts the frontend migrations we are working through, so CI can stop any of
// them going backwards and we can compare quarters.
//
// Everything is measured with `git grep` / `git ls-tree` against a tree-ish, so
// historical quarters can be counted without checking them out or installing
// their dependencies. The one exception is `typecheck_errors`, which needs a
// real `node_modules`; it is only collected with `--typecheck`.
//
//   node scripts/quality-metrics.mjs                      # counts HEAD
//   node scripts/quality-metrics.mjs --ref <sha>          # counts any commit
//   node scripts/quality-metrics.mjs --typecheck          # adds tsc errors
//   node scripts/quality-metrics.mjs --check <baseline>   # fails on increases

import { execFileSync } from 'node:child_process'
import { readFileSync } from 'node:fs'

const FE = 'frontend'
const SRC = [`${FE}/web`, `${FE}/common`]

// Paths that define the tokens, or that are allowed to hold raw values because
// they are fixtures rather than product code.
const NOT_PRODUCT = [
  `:(exclude)${FE}/web/styles/_tokens.scss`,
  `:(exclude)${FE}/web/styles/_primitives.scss`,
  `:(exclude)${FE}/web/styles/_variables.scss`,
  `:(exclude)${FE}/web/styles/_token-utilities.scss`,
  `:(exclude)${FE}/common/theme/tokens.ts`,
  `:(exclude)${FE}/common/theme/tokens.json`,
  `:(exclude)${FE}/*/__tests__/*`,
  `:(exclude)${FE}/*.stories.*`,
]

const TS = ['*.ts', '*.tsx']
const JS = ['*.js', '*.jsx']

// Each metric counts either the files that match (`files`) or every match in
// them (`matches`). Lower is better for all of them, which is what lets CI
// treat the baseline as a ceiling.
const METRICS = [
  {
    exts: JS,
    mode: 'files',
    name: 'js_jsx_files',
    note: 'TS migration: files still on JavaScript',
  },
  {
    exts: TS,
    goal: 'up',
    mode: 'files',
    name: 'ts_tsx_files',
    note: 'TS migration: files already converted (context, not a target)',
  },
  {
    fixed: true,
    mode: 'matches',
    name: 'any_annotations',
    note: 'TS migration: explicit `any` annotations',
    paths: SRC.flatMap((dir) => TS.map((glob) => `${dir}/${glob}`)),
    pattern: ': any',
  },
  {
    mode: 'matches',
    name: 'ts_suppressions',
    note: 'TS migration: @ts-ignore / @ts-expect-error',
    paths: SRC.flatMap((dir) => TS.map((glob) => `${dir}/${glob}`)),
    pattern: '@ts-ignore|@ts-expect-error',
  },
  {
    fixed: true,
    mode: 'matches',
    name: 'flux_store_imports',
    // Counted as imports rather than files on purpose: splitting one
    // Flux-reading component into five does not deepen the coupling, but it
    // would triple a file count and read as a regression.
    note: 'Flux to RTK: imports of any common/stores module',
    paths: SRC,
    pattern: "from 'common/stores/",
  },
  {
    fixed: true,
    mode: 'matches',
    name: 'account_store_imports',
    note: 'Flux to RTK: imports of AccountStore, blocked on its own migration',
    paths: SRC,
    pattern: "from 'common/stores/account-store'",
  },
  {
    fixed: true,
    mode: 'matches',
    name: 'project_store_imports',
    note: 'Flux to RTK: imports of ProjectStore',
    paths: SRC,
    pattern: "from 'common/stores/project-store'",
  },
  {
    mode: 'matches',
    name: 'dark_selectors',
    note: 'Semantic colour: .dark branches outside _tokens.scss',
    paths: [
      `${FE}/web/styles/*.scss`,
      `:(exclude)${FE}/web/styles/_tokens.scss`,
    ],
    pattern: '[.]dark',
  },
  {
    mode: 'matches',
    name: 'raw_colour_hex',
    note: 'Semantic colour: hex literals in product code',
    paths: [
      ...SRC.flatMap((dir) => [...TS, ...JS].map((glob) => `${dir}/${glob}`)),
      `${FE}/web/styles/*.scss`,
      ...NOT_PRODUCT,
    ],
    pattern: '#[0-9a-fA-F]{3,8}',
  },
]

const root = execFileSync('git', ['rev-parse', '--show-toplevel'], {
  encoding: 'utf8',
}).trim()

const git = (args) => {
  try {
    return execFileSync('git', args, {
      cwd: root,
      encoding: 'utf8',
      maxBuffer: 64 * 1024 * 1024,
    })
  } catch (error) {
    // `git grep` exits 1 when nothing matches, which is a count of zero rather
    // than a failure. Anything else is real.
    if (error.status === 1 && !error.stderr?.trim()) return ''
    throw error
  }
}

const lines = (out) => out.split('\n').filter(Boolean)

const count = (metric, ref) => {
  if (metric.exts) {
    // `ls-tree` only prefix-matches, so list the roots and filter here.
    const suffixes = metric.exts.map((glob) => glob.replace('*', ''))
    return lines(
      git(['ls-tree', '-r', '--name-only', ref, '--', ...SRC]),
    ).filter((path) => suffixes.some((suffix) => path.endsWith(suffix))).length
  }
  const flags = ['grep', metric.fixed ? '-F' : '-E', '--no-color']
  flags.push(metric.mode === 'files' ? '-l' : '-c')
  const out = lines(git([...flags, metric.pattern, ref, '--', ...metric.paths]))
  if (metric.mode === 'files') return out.length
  // `-c` gives `<ref>:<path>:<n>`; the count is the last field.
  return out.reduce((sum, line) => sum + Number(line.split(':').pop()), 0)
}

const typecheckErrors = () => {
  try {
    execFileSync('npx', ['tsc', '--noEmit', '-p', 'tsconfig.json'], {
      cwd: `${root}/${FE}`,
      encoding: 'utf8',
      maxBuffer: 64 * 1024 * 1024,
    })
    return 0
  } catch (error) {
    return lines(String(error.stdout ?? '')).filter((line) =>
      line.includes('error TS'),
    ).length
  }
}

const args = process.argv.slice(2)
const flag = (name) => {
  const i = args.indexOf(name)
  return i === -1 ? undefined : args[i + 1]
}

const ref = flag('--ref') ?? 'HEAD'
const sha = git(['rev-parse', ref]).trim()

const metrics = {}
for (const metric of METRICS) metrics[metric.name] = count(metric, sha)
if (args.includes('--typecheck')) metrics.typecheck_errors = typecheckErrors()

const report = {
  date: git(['log', '-1', '--format=%cs', sha]).trim(),
  metrics,
  ref,
  sha,
}

const baselinePath = flag('--check')
if (!baselinePath) {
  process.stdout.write(`${JSON.stringify(report, null, 2)}\n`)
  process.exit(0)
}

const baseline = JSON.parse(readFileSync(baselinePath, 'utf8'))
const goalUp = new Set(
  METRICS.filter((m) => m.goal === 'up').map((m) => m.name),
)
const rows = []
let regressed = false

for (const [name, value] of Object.entries(metrics)) {
  const was = baseline.metrics?.[name]
  if (was === undefined) {
    rows.push(`  NEW    ${name}: ${value} (add it to the baseline)`)
    continue
  }
  const delta = value - was
  const worse = goalUp.has(name) ? delta < 0 : delta > 0
  if (worse) regressed = true
  const sign = delta > 0 ? `+${delta}` : `${delta}`
  let mark = '  ==  '
  if (worse) mark = 'WORSE '
  else if (delta !== 0) mark = 'better'
  rows.push(`  ${mark} ${name}: ${was} -> ${value} (${sign})`)
}

process.stdout.write(
  `Frontend quality metrics vs baseline\n${rows.join('\n')}\n`,
)

if (regressed) {
  process.stdout.write(
    '\nOne of these went the wrong way. Either bring it back down, or if the\n' +
      'increase is deliberate, say why in the PR and update\n' +
      'scripts/quality-baseline.json in the same commit.\n',
  )
  process.exit(1)
}
process.stdout.write('\nNothing went backwards.\n')
