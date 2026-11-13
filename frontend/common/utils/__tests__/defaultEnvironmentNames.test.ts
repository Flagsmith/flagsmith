import { getDefaultEnvironmentNames } from 'common/utils/defaultEnvironmentNames'

describe('getDefaultEnvironmentNames', () => {
  it('uses the names from the flag value', () => {
    // When
    const names = getDefaultEnvironmentNames('["Dev", "Staging", "Prod"]')

    // Then
    expect(names).toEqual(['Dev', 'Staging', 'Prod'])
  })

  it.each([
    ['the flag is off', undefined],
    ['the value is not JSON', 'Dev, Prod'],
    ['the value is not a list', '{"name": "Dev"}'],
    ['the list is empty', '[]'],
    ['a name is blank', '["Dev", " "]'],
    ['a name is not text', '["Dev", 2]'],
  ])('falls back to Development and Production when %s', (_, flagValue) => {
    // When
    const names = getDefaultEnvironmentNames(flagValue)

    // Then
    expect(names).toEqual(['Development', 'Production'])
  })
})
