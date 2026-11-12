/**
 * Checks for whitespace issues in rule condition values, particularly for IN operator
 * @param value - The value to check for whitespace issues
 * @param operator - The operator being used (e.g., 'IN')
 * @returns Object with warning message if issues found, null otherwise
 */
export const checkWhitespaceIssues = (
  value: string | number | boolean,
  operator?: string,
): { message: string } | null => {
  if (operator !== 'IN') return null
  if (typeof value !== 'string') return null

  const LEADING_WHITESPACE = /^\s/
  const TRAILING_WHITESPACE = /\s$/

  if (value.length >= 1 && value.trim() === '') {
    return { message: 'This value is only whitespaces' }
  }

  const items = value.split(',')

  if (items.length > 1) {
    const counts = items.reduce(
      (acc, item) => {
        const hasLeading = LEADING_WHITESPACE.test(item)
        const hasTrailing = TRAILING_WHITESPACE.test(item)

        if (hasLeading && hasTrailing) acc.both++
        else if (hasLeading) acc.leading++
        else if (hasTrailing) acc.trailing++

        return acc
      },
      { both: 0, leading: 0, trailing: 0 },
    )

    const totalIssues = counts.both + counts.leading + counts.trailing
    const hasMultipleIssues =
      [counts.both > 0, counts.leading > 0, counts.trailing > 0].filter(Boolean)
        .length > 1

    if (totalIssues > 0) {
      if (hasMultipleIssues) {
        return {
          message: `${totalIssues} item(s) have whitespace issues`,
        }
      }

      if (counts.both > 0) {
        return {
          message: `${counts.both} item(s) have leading and trailing whitespaces`,
        }
      }
      if (counts.leading > 0) {
        return {
          message: `${counts.leading} item(s) have leading whitespaces`,
        }
      }
      if (counts.trailing > 0) {
        return {
          message: `${counts.trailing} item(s) have trailing whitespaces`,
        }
      }
    }
  }

  const hasLeading = LEADING_WHITESPACE.test(value)
  const hasTrailing = TRAILING_WHITESPACE.test(value)

  if (hasLeading && hasTrailing) {
    return {
      message: 'This value starts and ends with whitespaces',
    }
  }
  if (hasLeading) {
    return { message: 'This value starts with whitespaces' }
  }
  if (hasTrailing) {
    return { message: 'This value ends with whitespaces' }
  }

  return null
}
