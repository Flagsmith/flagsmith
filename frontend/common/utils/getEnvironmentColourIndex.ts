/**
 * Position of an environment in the list EnvironmentTagSelect renders, used to
 * pick its tag colour. Falls back to 0 when the list is not loaded yet or the
 * environment is not in it.
 */
export const getEnvironmentColourIndex = (
  environments: { id: number }[] | undefined,
  environmentId: number | undefined,
): number => {
  const index = environments?.findIndex((v) => v.id === environmentId) ?? -1
  return index === -1 ? 0 : index
}
