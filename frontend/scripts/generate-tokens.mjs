/**
 * Generate all token files from tokens.json (single source of truth).
 *
 * Outputs:
 *   1. common/theme/tokens.ts     — TypeScript exports
 *   2. web/styles/_tokens.scss    — CSS custom properties
 *   3. web/styles/_token-utilities.scss — utility classes consuming tokens
 *   4. documentation/TokenReference.generated.stories.tsx — flat JSX for Storybook MCP
 *
 * Usage:
 *   node scripts/generate-tokens.mjs
 *   npm run generate:tokens
 */

import { readFileSync, writeFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { execSync } from 'node:child_process'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ROOT = resolve(__dirname, '..')
const json = JSON.parse(
  readFileSync(resolve(ROOT, 'common/theme/tokens.json'), 'utf-8'),
)

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const kebabToCamel = (s) =>
  s.replace(/-([a-z0-9])/g, (_, c) => c.toUpperCase())

const sorted = (obj) =>
  Object.entries(obj).sort(([a], [b]) => a.localeCompare(b))

const esc = (s) => s.replace(/\\/g, '\\\\').replace(/'/g, "\\'")
const lightVal = (e) => e.light ?? e.value
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1)

const NON_COLOUR = ['radius', 'shadow', 'duration', 'easing']
const DESCRIBED = ['radius', 'shadow', 'duration', 'easing']

function makeCssVar(cssVarName, fallback) {
  if (
    !fallback ||
    fallback.startsWith('rgba') ||
    fallback.startsWith('cubic-bezier')
  ) {
    return `var(${cssVarName})`
  }
  return `var(${cssVarName}, ${fallback})`
}

// ---------------------------------------------------------------------------
// Step 1: Build flat data from JSON
// ---------------------------------------------------------------------------

function buildScssLines() {
  const rootLines = []
  const darkLines = []

  // Colour tokens
  for (const [category, entries] of Object.entries(json.color)) {
    rootLines.push(`  // ${cap(category)}`)
    for (const [, e] of sorted(entries)) {
      rootLines.push(`  ${e.cssVar}: ${e.light};`)
      if (e.dark && e.dark !== e.light) {
        darkLines.push(`  ${e.cssVar}: ${e.dark};`)
      }
    }
    rootLines.push('')
  }

  // Non-colour tokens
  for (const cat of NON_COLOUR) {
    if (!json[cat]) continue
    rootLines.push(`  // ${cap(cat)}`)
    for (const [, e] of sorted(json[cat])) {
      const val = lightVal(e)
      rootLines.push(`  ${e.cssVar}: ${val};`)
      if (e.dark && e.dark !== val) {
        darkLines.push(`  ${e.cssVar}: ${e.dark};`)
      }
    }
    rootLines.push('')
  }

  return { rootLines, darkLines }
}

function buildTsColourLines() {
  const lines = []
  for (const [category, entries] of sorted(json.color)) {
    lines.push(`  ${category}: {`)
    for (const [key, e] of sorted(entries)) {
      const v = esc(makeCssVar(e.cssVar, e.light))
      lines.push(`    ${kebabToCamel(key)}: '${v}',`)
    }
    lines.push('  },')
  }
  return lines
}

function buildTsDescribedLines() {
  const blocks = []
  for (const cat of DESCRIBED) {
    if (!json[cat]) continue
    const lines = []
    lines.push(`// ${cap(cat)}`)
    lines.push(`export const ${cat}: Record<string, TokenEntry> = {`)
    for (const [key, e] of sorted(json[cat])) {
      const v = esc(makeCssVar(e.cssVar, lightVal(e)))
      const d = esc(e.description || '')
      lines.push(`  '${esc(key)}': {`)
      lines.push(`    description: '${d}',`)
      lines.push(`    value: '${v}',`)
      lines.push('  },')
    }
    lines.push('}')
    blocks.push(lines.join('\n'))
  }
  return blocks
}

function buildTableRows(title, entries, opts = {}) {
  const rows = []
  rows.push(`      <h3>${title}</h3>`)
  rows.push("      <table className='docs-table'>")
  rows.push('        <thead>')
  rows.push('          <tr>')
  rows.push('            <th>Token</th>')
  rows.push('            <th>Value</th>')
  if (opts.showDescription) rows.push('            <th>Usage</th>')
  rows.push('          </tr>')
  rows.push('        </thead>')
  rows.push('        <tbody>')
  for (const e of entries) {
    rows.push('          <tr>')
    rows.push(`            <td><code>${e.cssVar}</code></td>`)
    rows.push(`            <td><code>${e.value}</code></td>`)
    if (opts.showDescription && e.description) {
      rows.push(`            <td>${e.description}</td>`)
    }
    rows.push('          </tr>')
  }
  rows.push('        </tbody>')
  rows.push('      </table>')
  return rows
}

// ---------------------------------------------------------------------------
// Step 2: Render to strings
// ---------------------------------------------------------------------------

function generateScss() {
  const { rootLines, darkLines } = buildScssLines()

  const header = [
    '// =============================================================================',
    '// Design Tokens — AUTO-GENERATED from common/theme/tokens.json',
    '// Do not edit manually. Run: npm run generate:tokens',
    '// =============================================================================',
    '',
  ]

  const output = [...header, ':root {', ...rootLines, '}']

  if (darkLines.length > 0) {
    output.push('', '.dark {', ...darkLines, '}')
  }

  output.push('')
  return output.join('\n')
}

function generateTs() {
  const colourLines = buildTsColourLines()
  const describedBlocks = buildTsDescribedLines()

  const output = [
    '// =============================================================================',
    '// Design Tokens — AUTO-GENERATED from common/theme/tokens.json',
    '// Do not edit manually. Run: npm run generate:tokens',
    '// =============================================================================',
    '',
    'export const tokens = {',
    ...colourLines,
    '} as const',
    '',
    'export type TokenEntry = {',
    '  value: string',
    '  description: string',
    '}',
    '',
    ...describedBlocks,
    '',
    'export type TokenCategory = keyof typeof tokens',
    'export type TokenName<C extends TokenCategory> = keyof (typeof tokens)[C]',
    'export type RadiusScale = keyof typeof radius',
    'export type ShadowScale = keyof typeof shadow',
    '',
  ]

  return output.join('\n')
}

function generateMcpStory() {
  // Build all table rows
  const tables = []

  for (const [cat, entries] of Object.entries(json.color)) {
    const data = Object.values(entries).map((e) => ({
      cssVar: e.cssVar,
      value: e.light,
    }))
    tables.push(...buildTableRows(`Colour: ${cat}`, data))
  }

  for (const cat of DESCRIBED) {
    if (!json[cat]) continue
    const data = Object.values(json[cat]).map((e) => ({
      cssVar: e.cssVar,
      value: lightVal(e),
      description: e.description || '',
    }))
    tables.push(...buildTableRows(cap(cat), data, { showDescription: true }))
  }

  const output = [
    '// AUTO-GENERATED from common/theme/tokens.json — do not edit manually',
    '// Run: npm run generate:tokens',
    '',
    "import React from 'react'",
    "import type { Meta, StoryObj } from 'storybook'",
    '',
    "import './docs.scss'",
    "import DocPage from './components/DocPage'",
    '',
    'const meta: Meta = {',
    "  parameters: { chromatic: { disableSnapshot: true }, layout: 'padded' },",
    "  title: 'Design System/Token Reference (MCP)',",
    '}',
    'export default meta',
    '',
    'export const AllTokens: StoryObj = {',
    "  name: 'All tokens (MCP reference)',",
    '  render: () => (',
    '    <DocPage',
    "      title='Token Reference'",
    "      description='Complete token catalogue generated from common/theme/tokens.json. All data is inlined for Storybook MCP.'",
    '    >',
    ...tables,
    '',
    "      <h3>Dark mode shadows</h3>",
    '      <p>',
    '        Dark mode overrides use stronger opacity (0.20-0.40 vs 0.05-0.20).',
    '        Higher elevation surfaces should use lighter backgrounds',
    '        (--color-surface-emphasis) rather than relying solely on shadows.',
    '      </p>',
    '',
    '      <h3>Motion pairing</h3>',
    '      <p>',
    '        Combine a duration with an easing: transition: all var(--duration-normal) var(--easing-standard).',
    '        Use --easing-entrance for elements appearing, --easing-exit for elements leaving.',
    '      </p>',
    '    </DocPage>',
    '  ),',
    '}',
    '',
  ]

  return output.join('\n')
}

function generateUtilities() {
  const lines = [
    '// =============================================================================',
    '// Token Utility Classes — AUTO-GENERATED from common/theme/tokens.json',
    '// Do not edit manually. Run: npm run generate:tokens',
    '// Dark mode is automatic — CSS custom properties resolve differently under',
    '// :root vs .dark, so no dark-prefixed classes are needed.',
    '// =============================================================================',
    '',
  ]

  // Colour utilities
  const colourMappings = {
    surface: { prefix: 'bg-surface', property: 'background-color' },
    text: { prefix: 'text', property: 'color' },
    border: { prefix: 'border', property: 'border-color' },
    icon: { prefix: 'icon', property: null }, // special: color + fill
  }

  for (const [category, entries] of Object.entries(json.color)) {
    const mapping = colourMappings[category]
    if (!mapping) continue

    lines.push(`// ${cap(category)}`)
    for (const [key, e] of sorted(entries)) {
      const cls = `${mapping.prefix}-${key}`
      if (category === 'icon') {
        lines.push(`.${cls} { color: var(${e.cssVar}); fill: var(${e.cssVar}); }`)
      } else {
        lines.push(`.${cls} { ${mapping.property}: var(${e.cssVar}); }`)
      }
    }
    lines.push('')
  }

  // Radius utilities
  if (json.radius) {
    lines.push('// Radius')
    for (const [key, e] of sorted(json.radius)) {
      lines.push(`.rounded-${key} { border-radius: var(${e.cssVar}); }`)
    }
    lines.push('')
  }

  // Shadow utilities
  if (json.shadow) {
    lines.push('// Shadow')
    for (const [key, e] of sorted(json.shadow)) {
      lines.push(`.shadow-${key} { box-shadow: var(${e.cssVar}); }`)
    }
    lines.push('.shadow-none { box-shadow: none; }')
    lines.push('')
  }

  // Transition utilities
  if (json.duration && json.easing) {
    lines.push('// Transitions')
    for (const [key, e] of sorted(json.duration)) {
      lines.push(
        `.transition-${key} { transition-duration: var(${e.cssVar}); transition-timing-function: var(--easing-standard); }`,
      )
    }
    lines.push('')
  }

  return lines.join('\n')
}

// ---------------------------------------------------------------------------
// Write and format
// ---------------------------------------------------------------------------

const scssPath = resolve(ROOT, 'web/styles/_tokens.scss')
const utilitiesPath = resolve(ROOT, 'web/styles/_token-utilities.scss')
const tsPath = resolve(ROOT, 'common/theme/tokens.ts')
const storyPath = resolve(ROOT, 'documentation/TokenReference.generated.stories.tsx')

writeFileSync(scssPath, generateScss(), 'utf-8')
writeFileSync(utilitiesPath, generateUtilities(), 'utf-8')
writeFileSync(tsPath, generateTs(), 'utf-8')
writeFileSync(storyPath, generateMcpStory(), 'utf-8')

try {
  execSync(`npx prettier --write "${tsPath}" "${storyPath}"`, {
    cwd: ROOT,
    stdio: 'pipe',
  })
} catch {
  // prettier may not be available in all environments
}

const colorCount = Object.values(json.color).reduce(
  (sum, cat) => sum + Object.keys(cat).length,
  0,
)
const nonColorCount = NON_COLOUR.reduce(
  (sum, cat) => sum + (json[cat] ? Object.keys(json[cat]).length : 0),
  0,
)
console.log('Generated from tokens.json:')
console.log(`  ${scssPath}`)
console.log(`  ${utilitiesPath}`)
console.log(`  ${tsPath}`)
console.log(`  ${storyPath}`)
console.log(
  `  ${colorCount} colour + ${nonColorCount} non-colour = ${colorCount + nonColorCount} tokens`,
)
