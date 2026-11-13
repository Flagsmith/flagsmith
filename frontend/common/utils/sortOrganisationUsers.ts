import sortBy from 'lodash/sortBy'
import type { User } from 'common/types/responses'

type OrganisationUser = Pick<User, 'id' | 'first_name' | 'last_name'>

// The current user first, then everyone else by full name
export function sortOrganisationUsers<T extends OrganisationUser>(
  users: T[],
  currentUserId: number | undefined,
): T[] {
  return sortBy(users, (user) =>
    user.id === currentUserId
      ? ''
      : `${user.first_name || ''} ${user.last_name || ''}`.toLowerCase(),
  )
}
