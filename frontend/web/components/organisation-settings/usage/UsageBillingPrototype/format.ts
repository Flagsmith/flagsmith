import Format from 'common/utils/format'

/**
 * PROTOTYPE (#8184). `Format.shortenNumber` does the formatting, this only
 * guards zero: it takes log10 of the value, so 0 comes back as NaN.
 */
export const compact = (n: number): string =>
  n ? Format.shortenNumber(n) : '0'

export const currency = (amount: number): string =>
  `$${amount.toLocaleString()}`
