export const sentences = (...parts: (string | false | undefined)[]): string =>
  parts.filter(Boolean).join(' ')

export const calls = (count: number): string => (count === 1 ? 'call' : 'calls')
