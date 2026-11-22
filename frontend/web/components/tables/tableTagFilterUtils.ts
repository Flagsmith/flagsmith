export const matchesTagFilter = (label: string, filter: string): boolean =>
  label.toLowerCase().includes(filter.toLowerCase())
