import { sortOrganisationUsers } from 'common/utils/sortOrganisationUsers'

const user = (id: number, first_name: string, last_name: string) => ({
  first_name,
  id,
  last_name,
})

describe('sortOrganisationUsers', () => {
  it('puts the current user first, then sorts by full name', () => {
    // Given
    const users = [
      user(1, 'Wadii', 'Zaim'),
      user(2, 'Talisson', 'Costa'),
      user(3, 'asaph', 'Kotzin'),
    ]

    // When
    const sorted = sortOrganisationUsers(users, 2)

    // Then
    expect(sorted.map((u) => u.id)).toEqual([2, 3, 1])
  })

  it('ignores case and missing names', () => {
    // Given
    const users = [
      user(1, 'bob', ''),
      user(2, '', 'Adams'),
      user(3, 'Alice', ''),
    ]

    // When
    const sorted = sortOrganisationUsers(users, undefined)

    // Then
    expect(sorted.map((u) => u.id)).toEqual([2, 3, 1])
  })

  it('leaves the input untouched', () => {
    // Given
    const users = [user(1, 'Zed', ''), user(2, 'Amy', '')]

    // When
    sortOrganisationUsers(users, undefined)

    // Then
    expect(users.map((u) => u.id)).toEqual([1, 2])
  })
})
