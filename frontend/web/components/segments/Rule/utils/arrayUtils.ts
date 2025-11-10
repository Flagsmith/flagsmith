export const safeParseArray = (
  value: string | number | boolean | null,
): string[] => {
  if (typeof value !== 'string') {
    return []
  }

  // Parse CSV format: split by comma, trim whitespace, filter empty strings
  return value
    .split(',')
    .map((item) => item.trim())
    .filter((item) => item.length > 0)
}
