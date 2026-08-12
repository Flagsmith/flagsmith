import { ProjectSummary } from 'common/types/responses'
import { newestProject } from 'components/pages/onboarding/bootstrap/onboardingProject'

const project = (id: number): ProjectSummary => ({ id } as ProjectSummary)

describe('newestProject', () => {
  it('takes the project the user just created, not the first returned', () => {
    const created = project(9)
    expect(newestProject([project(2), created, project(5)])).toBe(created)
  })

  it('takes the only project there is', () => {
    const only = project(3)
    expect(newestProject([only])).toBe(only)
  })

  it('finds nothing in an organisation with no projects', () => {
    expect(newestProject([])).toBeUndefined()
  })
})
