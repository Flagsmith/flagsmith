// Fails on added SCSS lines with a hex colour or a .dark selector. Checks the
// staged diff by default, or the diff from SCSS_DIFF_BASE in CI, so existing
// lines don't fail a commit or PR.
const { execFileSync } = require('child_process')

// Where raw colour values and the dark theme are defined.
const allowed = [
  /^\.storybook\//,
  /^documentation\//,
  /^web\/styles\/_primitives\.scss$/,
  /^web\/styles\/_tokens\.scss$/,
]

const checks = [
  {
    message: 'Use a colour token, not a hex literal.',
    pattern: /#([0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b/,
  },
  {
    message: 'Use a token whose value already changes in dark mode.',
    pattern: /\.dark\b/,
  },
]

const base = process.env.SCSS_DIFF_BASE
const files = process.argv.slice(2)
const diff = execFileSync(
  'git',
  [
    'diff',
    '--relative',
    '--unified=0',
    ...(base ? [`${base}...HEAD`] : ['--cached']),
    '--',
    ...(files.length ? files : ['*.scss']),
  ],
  { encoding: 'utf8' },
)

const problems = []
let file
let line
for (const row of diff.split('\n')) {
  if (row.startsWith('+++ ')) {
    file = row.replace(/^\+\+\+ b\//, '')
  } else if (row.startsWith('@@')) {
    line = Number(row.match(/\+(\d+)/)[1])
  } else if (row.startsWith('+')) {
    const isAllowed = allowed.some((pattern) => pattern.test(file))
    // Comments can mention a colour.
    const code = row.slice(1).replace(/\/\/.*$/, '')
    checks
      .filter(({ pattern }) => !isAllowed && pattern.test(code))
      .forEach(({ message }) => problems.push(`${file}:${line}  ${message}`))
    line++
  }
}

if (problems.length) {
  // eslint-disable-next-line no-console
  console.error(problems.join('\n'))
  process.exit(1)
}
