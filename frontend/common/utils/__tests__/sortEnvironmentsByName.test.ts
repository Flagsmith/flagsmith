import { sortEnvironmentsByName } from 'common/utils/sortEnvironmentsByName'
import { makeEnvironment } from './environmentFixture'

const names = (environments: { name: string }[]) =>
  environments.map((env) => env.name)

describe('sortEnvironmentsByName', () => {
  it('orders environments by name rather than by id', () => {
    // Given
    const environments = [
      makeEnvironment(1, 'Production'),
      makeEnvironment(2, 'Development'),
      makeEnvironment(3, 'Staging'),
    ]

    // When
    const sorted = sortEnvironmentsByName(environments)

    // Then
    expect(names(sorted)).toEqual(['Development', 'Production', 'Staging'])
  })

  it('puts capitalised names before lowercase ones, as the UI always has', () => {
    // Given
    const environments = [
      makeEnvironment(1, 'test'),
      makeEnvironment(2, 'Production'),
      makeEnvironment(3, 'new env'),
      makeEnvironment(4, 'Development'),
    ]

    // When
    const sorted = sortEnvironmentsByName(environments)

    // Then
    expect(names(sorted)).toEqual([
      'Development',
      'Production',
      'new env',
      'test',
    ])
  })

  it('keeps the API order for environments with the same name', () => {
    // Given
    const environments = [
      makeEnvironment(2, 'Staging'),
      makeEnvironment(1, 'Staging'),
    ]

    // When
    const sorted = sortEnvironmentsByName(environments)

    // Then
    expect(sorted.map((env) => env.id)).toEqual([2, 1])
  })

  it('leaves the input untouched', () => {
    // Given
    const environments = [
      makeEnvironment(1, 'Production'),
      makeEnvironment(2, 'Development'),
    ]

    // When
    sortEnvironmentsByName(environments)

    // Then
    expect(names(environments)).toEqual(['Production', 'Development'])
  })

  it('returns an empty list for a project without environments', () => {
    // When
    const sorted = sortEnvironmentsByName([])

    // Then
    expect(sorted).toEqual([])
  })
})
