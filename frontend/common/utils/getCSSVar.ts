/**
 * Read the computed value of a CSS custom property from the document root.
 * Use this when JS code needs actual colour strings (e.g. Recharts fills)
 * rather than var() references.
 *
 * Respects dark mode — returns the currently resolved value.
 *
 * @example
 *   import { getCSSVar } from 'common/utils/getCSSVar'
 *   const fill = getCSSVar('--color-chart-1') // '#0aaddf' in light, '#45bce0' in dark
 */
export function getCSSVar(name: string): string {
  if (typeof document === 'undefined') return ''
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim()
}

/**
 * Read multiple CSS custom properties at once.
 */
export function getCSSVars(names: readonly string[]): string[] {
  if (typeof document === 'undefined') return names.map(() => '')
  const style = getComputedStyle(document.documentElement)
  return names.map((name) => style.getPropertyValue(name).trim())
}
