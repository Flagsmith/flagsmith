import { getProjectLandingPath } from 'common/utils/projectLandingPath'
import { makeEnvironment } from './environmentFixture'

describe('getProjectLandingPath', () => {
  it('opens the features of the first environment', () => {
    // Given
    const environments = [
      makeEnvironment(2, 'Development'),
      makeEnvironment(1, 'Production'),
    ]

    // When
    const path = getProjectLandingPath(7, environments)

    // Then
    expect(path).toBe('/project/7/environment/key-2/features')
  })

  it('opens create environment when the project has none', () => {
    // When
    const path = getProjectLandingPath(7, [])

    // Then
    expect(path).toBe('/project/7/environment/create')
  })
})
