/** What the user typed, reduced to the form a match is made against. */
export const searchTerm = (input: string): string => input.trim().toLowerCase()

// Normalises its own input, so a caller cannot compare a raw term against a
// reduced label. searchTerm is idempotent, so passing a reduced one is free.
export const matchesSearch = (label: string, input: string): boolean =>
  label.toLowerCase().includes(searchTerm(input))

type RowSearch = {
  label: string
  search: string
  isActive: boolean
}

// An active filter stays visible whatever is typed, or there is no way to see
// it or turn it off without clearing the search first.
export const showsRow = ({ isActive, label, search }: RowSearch): boolean =>
  isActive || matchesSearch(label, search)
