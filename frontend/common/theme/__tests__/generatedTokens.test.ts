import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

import tokens from 'common/theme/tokens.json'

const read = (path: string) =>
  readFileSync(resolve(__dirname, '../../..', path), 'utf-8')

const outputs = {
  'the token reference': read(
    'documentation/TokenReference.generated.stories.tsx',
  ),
  'tokens.ts': read('common/theme/tokens.ts'),
}

// Every custom property a group declares, however deeply it nests: `color`
// groups by category, the ramps are flat.
const cssVars = (node: unknown): string[] => {
  if (typeof node !== 'object' || node === null) return []
  const entry = node as { cssVar?: unknown }
  if (typeof entry.cssVar === 'string') return [entry.cssVar]
  return Object.values(node).flatMap(cssVars)
}

// Derived, not listed: a group added to tokens.json is covered here the day it
// arrives. Listing them would miss exactly the case that prompted this, a new
// group reaching the CSS while the other generators were left behind.
const groups = Object.entries(tokens)
  .map(([name, node]) => [name, cssVars(node)] as const)
  .filter(([, vars]) => vars.length > 0)

describe('generated token outputs', () => {
  it('finds groups to check', () => {
    expect(groups.length).toBeGreaterThan(0)
  })

  describe.each(groups)('%s', (_name, vars) => {
    it.each(Object.keys(outputs))('reaches %s', (output) => {
      const missing = vars.filter(
        (cssVar) => !outputs[output as keyof typeof outputs].includes(cssVar),
      )
      expect(missing).toEqual([])
    })
  })

  // The one carve-out. Primitives are raw values with no theme, and a component
  // reaching past the semantic layer is what the layering exists to prevent.
  it('keeps primitives out of tokens.ts', () => {
    const leaked = Object.keys(tokens.primitives).filter((name) =>
      outputs['tokens.ts'].includes(`var(--${name},`),
    )
    expect(leaked).toEqual([])
  })
})
