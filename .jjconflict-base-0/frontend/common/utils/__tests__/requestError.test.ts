import { isNotFoundError, toErrorMessage } from 'common/utils/requestError'

describe('isNotFoundError', () => {
  it('is true for a 404', () => {
    expect(isNotFoundError({ data: {}, status: 404 })).toBe(true)
  })

  it.each([
    ['no error', undefined],
    ['a server error', { data: {}, status: 500 }],
    ['a permission error', { data: {}, status: 403 }],
    ['a network error', { error: 'Failed to fetch', status: 'FETCH_ERROR' }],
    ['a serialized error', { message: 'Boom', name: 'Error' }],
  ] as const)('is false for %s', (_, error) => {
    expect(isNotFoundError(error)).toBe(false)
  })
})

describe('toErrorMessage', () => {
  it("returns the API's detail message", () => {
    // Given
    const error = { data: { detail: 'Already committed.' }, status: 400 }

    // When
    const message = toErrorMessage(error)

    // Then
    expect(message).toBe('Already committed.')
  })

  it('returns field errors as they are', () => {
    // Given
    const error = { data: { title: ['This field is required.'] }, status: 400 }

    // When
    const message = toErrorMessage(error)

    // Then
    expect(message).toBe(error)
  })

  it('returns errors without a body as they are', () => {
    // Given
    const error = { message: 'Boom', name: 'Error' }

    // When
    const message = toErrorMessage(error)

    // Then
    expect(message).toBe(error)
  })

  it('returns nothing when there is no error', () => {
    expect(toErrorMessage(undefined)).toBeUndefined()
  })
})
