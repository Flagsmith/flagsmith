/**
 * Turns an audit-log / diff value into the string shown in the diff viewer.
 * Objects and arrays (e.g. a segment's `rules_data`) are pretty-printed as JSON,
 * otherwise template interpolation would render them as `[object Object]`.
 */
export const stringifyDiffValue = (value: unknown): string => {
  if (value === undefined || value === null) {
    return ''
  }
  if (value === '') {
    return '""'
  }
  if (typeof value === 'object') {
    return JSON.stringify(value, null, 2)
  }
  return `${value}`
}
