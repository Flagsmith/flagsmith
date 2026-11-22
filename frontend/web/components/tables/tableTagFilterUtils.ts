export const matchesTagFilter = (label: string, filter: string): boolean =>
  label.toUpperCase().includes(filter.toUpperCase())
