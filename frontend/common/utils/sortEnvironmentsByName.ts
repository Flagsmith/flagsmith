import sortBy from 'lodash/sortBy'
import type { Environment } from 'common/types/responses'

// The API orders environments by id
export function sortEnvironmentsByName(
  environments: Environment[],
): Environment[] {
  return sortBy(environments, 'name')
}
