/** PROTOTYPE (#8184). Compact numbers to match the designs: 1.24M, 68.4k. */
export const compact = (n: number): string => {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`
  return `${Math.round(n)}`
}

export const currency = (amount: number): string =>
  `$${amount.toLocaleString()}`
