import type { Environment } from 'common/types/responses'

// Picks the environment most likely to represent production: the first whose
// name looks like production, falling back to the first environment. Used as
// the default for lifecycle classification when the user has no stored choice.
export function predictProdEnvironment(
  environments: Environment[],
): number | undefined {
  if (!environments.length) return undefined
  const prod = environments.find((e) => e.name.toLowerCase().includes('prod'))
  return prod?.id ?? environments[0].id
}
