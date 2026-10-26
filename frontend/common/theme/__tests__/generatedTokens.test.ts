import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

import tokens from 'common/theme/tokens.json'

const read = (path: string) =>
  readFileSync(resolve(__dirname, '../../..', path), 'utf-8')

// Each output wraps a token in its own delimiters. Matching them, not the bare
// name, keeps --primary-500 from standing in for a missing --primary-50.
const outputs = {
  'the token reference': {
    source: read('documentation/TokenReference.generated.stories.tsx'),
    wrap: (cssVar: string) => `<code>${cssVar}</code>`,
  },
  'tokens.ts': {
    source: read('common/theme/tokens.ts'),
    wrap: (cssVar: string) => `var(${cssVar},`,
  },
}

// Every custom property a group declares, however deeply it nests: `color`
// groups by category, the ramps are flat.
const cssVars = (node: unknown): string[] => {
  if (typeof node !== 'object' || node === null) return []
  const entry = node as { cssVar?: unknown }
  if (typeof entry.cssVar === 'string') return [entry.cssVar]
  return Object.values(node).flatMap(cssVars)
}

// Derived, not listed: a hardcoded list would miss the case that prompted this,
// a new group reaching the CSS while the other generators were left behind.
const groups = Object.entries(tokens)
  .map(([name, node]) => [name, cssVars(node)] as const)
  .filter(([, vars]) => vars.length > 0)

describe('generated token outputs', () => {
  it('finds groups to check', () => {
    expect(groups.length).toBeGreaterThan(0)
  })

  describe.each(groups)('%s', (_name, vars) => {
    it.each(Object.keys(outputs))('reaches %s', (output) => {
      const { source, wrap } = outputs[output as keyof typeof outputs]
      const missing = vars.filter((cssVar) => !source.includes(wrap(cssVar)))
      expect(missing).toEqual([])
    })
  })

  // The one carve-out. Primitives are raw values with no theme, and a component
  // reaching past the semantic layer is what the layering exists to prevent.
  it('keeps primitives out of tokens.ts', () => {
    const leaked = Object.keys(tokens.primitives).filter((name) =>
      outputs['tokens.ts'].source.includes(`var(--${name},`),
    )
    expect(leaked).toEqual([])
  })

  // Legacy Sass reads primitives from this map, so a stale copy brings back
  // two palettes.
  it('mirrors every primitive in the Sass map', () => {
    const sass = read('web/styles/_primitives.scss')
    const entries = [...sass.matchAll(/^ {2}'([\w-]+)': (#[0-9a-f]{6}),$/gim)]
    expect(
      Object.fromEntries(entries.map(([, name, hex]) => [name, hex])),
    ).toEqual(tokens.primitives)
  })
})
