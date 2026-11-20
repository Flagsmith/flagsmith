export type HeadingLevel = 1 | 2 | 3 | 4 | 5 | 6
export type HeadingSize = 'lg' | 'md' | 'sm'

export const getHeadingSize = (level: HeadingLevel): HeadingSize => {
  if (level === 1) return 'lg'
  if (level === 2) return 'md'
  return 'sm'
}
