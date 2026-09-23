import { SortOrder } from 'common/types/requests'
import { User } from 'common/types/responses'
import { SortOption } from 'components/PanelSearch'

export type SortableUser<T extends User> = T & {
  sortName: string
  sortRole: string
}

// Shared sort options for the user permissions tables. `sortName` and
// `sortRole` are computed by decorateUsersForSort so we can sort on a composite
// name and a derived role label rather than the raw fields.
export const userTableSorting: SortOption[] = [
  { default: true, label: 'Name', order: SortOrder.ASC, value: 'sortName' },
  { label: 'Role', order: SortOrder.ASC, value: 'sortRole' },
]

export const decorateUsersForSort = <T extends User>(
  users: T[] | undefined,
  getRoleLabel: (user: T) => string,
): SortableUser<T>[] =>
  (users || []).map((user) => ({
    ...user,
    sortName: `${user.first_name} ${user.last_name}`.trim().toLowerCase(),
    sortRole: getRoleLabel(user),
  }))
