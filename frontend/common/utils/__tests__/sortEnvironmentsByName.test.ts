import { sortEnvironmentsByName } from 'common/utils/sortEnvironmentsByName'
import { makeEnvironment } from './environmentFixture'

const names = (environments: { name: string }[]) =>
  environments.map((env) => env.name)

describe('sortEnvironmentsByName', () => {
  it('orders environments by name rather than by id', () => {
    const environments = [
      makeEnvironment(1, 'Production'),
      makeEnvironment(2, 'Development'),
      makeEnvironment(3, 'Staging'),
    ]

    expect(names(sortEnvironmentsByName(environments))).toEqual([
      'Development',
      'Production',
      'Staging',
    ])
  })

  it('puts capitalised names before lowercase ones, as the UI always has', () => {
    const environments = [
      makeEnvironment(1, 'test'),
      makeEnvironment(2, 'Production'),
      makeEnvironment(3, 'new env'),
      makeEnvironment(4, 'Development'),
    ]

    expect(names(sortEnvironmentsByName(environments))).toEqual([
      'Development',
      'Production',
      'new env',
      'test',
    ])
  })
})
