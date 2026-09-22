// WCAG relative luminance and contrast ratio, per
// https://www.w3.org/TR/WCAG21/#dfn-relative-luminance

export const AA_NORMAL_TEXT = 4.5

export const relativeLuminance = (hex: string): number => {
  const value = hex.replace('#', '')
  const [r, g, b] = [0, 2, 4]
    .map((i) => parseInt(value.substring(i, i + 2), 16) / 255)
    .map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

export const contrastRatio = (a: string, b: string): number => {
  const [lighter, darker] = [relativeLuminance(a), relativeLuminance(b)].sort(
    (x, y) => y - x,
  )
  return (lighter + 0.05) / (darker + 0.05)
}
