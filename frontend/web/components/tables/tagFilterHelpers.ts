export const isTagMatchingFilter = (tagLabel: string, filter: string) => {
  const search = filter.trim().toLowerCase()
  return !search || tagLabel.toLowerCase().includes(search)
}

export const isSpecialFilterItemVisible = (
  itemName: 'archived' | 'untagged',
  filter: string,
) => isTagMatchingFilter(itemName, filter)
