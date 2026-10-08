// Perceptual distance between two colours, for deciding whether two hues can
// be told apart. WCAG contrast cannot answer that: it compares lightness only,
// so two colours of the same lightness score 1:1 against each other however
// far apart their hues are.

const EPSILON = 1e-6

const toLinear = (channel: number) =>
  channel <= 0.03928 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4

const linearRgb = (hex: string): [number, number, number] => {
  const value = hex.replace('#', '')
  const [r, g, b] = [0, 2, 4].map((i) =>
    toLinear(parseInt(value.substring(i, i + 2), 16) / 255),
  )
  return [r, g, b]
}

const cubeRoot = (n: number) => (n > EPSILON ? Math.cbrt(n) : 0)

/** https://bottosson.github.io/posts/oklab/ */
export const oklab = (hex: string): [number, number, number] => {
  const [r, g, b] = linearRgb(hex)
  const l = cubeRoot(0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b)
  const m = cubeRoot(0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b)
  const s = cubeRoot(0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b)
  return [
    0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s,
    1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s,
    0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s,
  ]
}

/**
 * Euclidean distance in OKLab, where 1 spans black to white. Two colours under
 * about 0.10 apart read as the same colour at the size of a tag dot.
 */
export const perceptualDistance = (a: string, b: string): number => {
  const [al, aa, ab] = oklab(a)
  const [bl, ba, bb] = oklab(b)
  return Math.hypot(al - bl, aa - ba, ab - bb)
}
