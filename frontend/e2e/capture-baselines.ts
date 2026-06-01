import { execSync } from 'child_process'
import * as fs from 'fs'
import * as path from 'path'

const SNAPSHOTS_DIR = path.resolve(__dirname, 'visual-regression-snapshots')
const SCREENSHOTS_DIR = path.resolve(__dirname, 'visual-regression-screenshots')

function run(cmd: string) {
  execSync(cmd, { stdio: 'inherit' })
}

function runQuiet(cmd: string) {
  execSync(cmd, { stdio: 'pipe' })
}

const branch = execSync('git rev-parse --abbrev-ref HEAD', { encoding: 'utf-8' }).trim()

console.log(`Current branch: ${branch}`)
console.log('Checking out main source code (keeping branch e2e tests)...')

// Only checkout main's source code, not e2e/ test files.
// This ensures both baseline and branch runs use the same test code.
runQuiet('git checkout main -- web/ common/')

try {
  console.log('Running E2E on main source with VISUAL_REGRESSION=1...')
  if (fs.existsSync(SCREENSHOTS_DIR)) {
    fs.rmSync(SCREENSHOTS_DIR, { recursive: true })
  }
  run('cross-env VISUAL_REGRESSION=1 npm run test')

  console.log('Copying screenshots to baselines...')
  if (fs.existsSync(SNAPSHOTS_DIR)) {
    fs.rmSync(SNAPSHOTS_DIR, { recursive: true })
  }
  fs.cpSync(SCREENSHOTS_DIR, SNAPSHOTS_DIR, { recursive: true })

  const count = fs.readdirSync(SNAPSHOTS_DIR).filter((f) => f.endsWith('.png')).length
  console.log(`Captured ${count} baseline snapshots`)
} finally {
  // Restore branch's source code
  console.log('Restoring branch source code...')
  runQuiet('git checkout -- web/ common/')
}

console.log('Baselines ready. Now run: VISUAL_REGRESSION=1 npm run test && npm run test:visual:compare')
