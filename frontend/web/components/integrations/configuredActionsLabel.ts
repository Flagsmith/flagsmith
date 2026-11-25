// Several configured instances of one integration need their own names
export const configuredActionsLabel = (
  title: string | undefined,
  index: number,
  count: number,
): string => {
  const name = `Actions for ${title ?? 'integration'}`
  return count > 1 ? `${name}, ${index + 1} of ${count}` : name
}
