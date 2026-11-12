export const joinSentences = (
  ...parts: (string | false | undefined)[]
): string => parts.filter(Boolean).join(' ')

export const apiCallsWord = (count: number): string =>
  count === 1 ? 'call' : 'calls'
