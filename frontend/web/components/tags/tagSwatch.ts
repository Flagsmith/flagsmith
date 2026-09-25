import { Tag as TTag } from 'common/types/responses'
import { contentColours } from 'common/theme/tokens'
import type { ContentColour } from 'common/theme/tokens'

/** The design system's Content palette, one swatch per colour. */
export type TagSwatch = ContentColour

/** Hue in degrees and chroma, from the OKLCH transform of an sRGB hex. */
function oklch(hex: string): { chroma: number; hue: number } | null {
  const h = hex.replace('#', '')
  if (!/^[0-9a-f]{6}$/i.test(h)) return null

  const toLinear = (v: number) =>
    v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4
  const [r, g, b] = [0, 2, 4].map((i) =>
    toLinear(parseInt(h.slice(i, i + 2), 16) / 255),
  )

  const l = Math.cbrt(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
  const m = Math.cbrt(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
  const s = Math.cbrt(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)

  const a = 1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s
  const bb = 0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s

  return {
    chroma: Math.hypot(a, bb),
    hue: ((Math.atan2(bb, a) * 180) / Math.PI + 360) % 360,
  }
}

// Below this a colour has no meaningful hue, so hue-matching it would pick a
// swatch at random. Grey is the honest answer.
const ACHROMATIC = 0.02
const GREY: TagSwatch = 'light-grey'

const SWATCHES = Object.entries(contentColours)
  .map(([name, hex]) => ({ name: name as TagSwatch, ...oklch(hex)! }))
  // Grey has no hue of its own, so it would otherwise attract anything near
  // its nominal angle, which is where indigo and navy sit.
  .filter(({ name }) => name !== GREY)

const cache = new Map<string, TagSwatch | null>()

/**
 * The Content swatch nearest a tag's colour in hue.
 *
 * Keyed on the colour already stored on the tag, so nothing needs migrating,
 * and it answers for colours the picker never offered: `color` is a bare
 * CharField with no validator, so a tag created through the API or an import
 * can hold anything. Matching rather than listing also means the eleven
 * swatches stay the only fills a tag can take, so contrast is settled by the
 * palette instead of by whatever hue was stored.
 */
export const getTagSwatch = (colour?: string | null): TagSwatch | null => {
  if (!colour) return null
  const key = colour.toLowerCase()
  if (cache.has(key)) return cache.get(key)!

  const parsed = oklch(key)
  let swatch: TagSwatch | null = null
  if (parsed) {
    swatch =
      parsed.chroma < ACHROMATIC
        ? GREY
        : SWATCHES.reduce((best, s) => {
            const d = (x: number) => Math.min(x, 360 - x)
            return d(Math.abs(parsed.hue - s.hue)) <
              d(Math.abs(parsed.hue - best.hue))
              ? s
              : best
          }).name
  }

  cache.set(key, swatch)
  return swatch
}

// A colour that is not a hex at all still has to render as something.
const NEUTRAL_UTILITIES = 'bg-surface-subtle text-default'

export const getTagSwatchUtilities = (colour?: string | null): string => {
  const swatch = getTagSwatch(colour)
  return swatch ? `tag-${swatch}` : NEUTRAL_UTILITIES
}

export const isSystemTag = (tag: Partial<TTag>): boolean =>
  !!tag.type && tag.type !== 'NONE'

export const SYSTEM_TAG_UTILITIES =
  'bg-surface-default border-default text-default'
