import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

import tokens from 'common/theme/tokens.json'

const read = (path: string) =>
  readFileSync(resolve(__dirname, '../../..', path), 'utf-8')

const tokensTs = read('common/theme/tokens.ts')
const reference = read('documentation/TokenReference.generated.stories.tsx')

// The design system's ramps, which sit between the primitives and the semantic
// tokens. Kept in step with RAMPS in scripts/generate-tokens.mjs.
const RAMPS = ['primary', 'neutral', 'state', 'always'] as const

type Entry = { cssVar: string }

const cssVars = (group: Record<string, Entry>) =>
  Object.values(group).map((entry) => entry.cssVar)

describe('generated token outputs', () => {
  describe.each(RAMPS)('%s ramp', (ramp) => {
    const vars = cssVars(
      (tokens as unknown as Record<string, Record<string, Entry>>)[ramp],
    )

    it('has tokens to emit', () => {
      expect(vars.length).toBeGreaterThan(0)
    })

    // These reached the CSS but not TypeScript once already, so nothing could
    // import them without writing the custom property by hand.
    it.each(vars)('emits %s into tokens.ts', (cssVar) => {
      expect(tokensTs).toContain(cssVar)
    })

    // The reference is what agents read, so it claiming to be complete and
    // missing a ramp is the same defect in a different file.
    it.each(vars)('emits %s into the token reference', (cssVar) => {
      expect(reference).toContain(cssVar)
    })
  })

  // The other half of the rule: primitives are raw values with no theme, and a
  // component reaching past the semantic layer is what the layering prevents.
  it('keeps primitives out of tokens.ts', () => {
    const leaked = Object.keys(tokens.primitives).filter((name) =>
      tokensTs.includes(`var(--${name},`),
    )
    expect(leaked).toEqual([])
  })
})
