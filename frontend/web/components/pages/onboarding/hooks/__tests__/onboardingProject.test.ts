import { ProjectSummary } from 'common/types/responses'
import { selectOnboardingProject } from 'components/pages/onboarding/hooks/onboardingProject'

const project = (id: number): ProjectSummary =>
  ({ id, name: `project ${id}` } as ProjectSummary)

const projects = [project(10), project(20), project(30)]

describe('selectOnboardingProject', () => {
  it('runs against the project named in the URL', () => {
    expect(selectOnboardingProject(projects, 20)).toBe(projects[1])
  })

  it('matches the id as a string, which is how it arrives', () => {
    expect(selectOnboardingProject(projects, '30')).toBe(projects[2])
  })

  it('ignores a project outside this organisation', () => {
    // A link carried over from another org, or an edited URL.
    expect(selectOnboardingProject(projects, 999)).toBe(projects[0])
  })

  it.each([null, undefined, ''])('falls back to the first with %p', (id) => {
    expect(selectOnboardingProject(projects, id)).toBe(projects[0])
  })

  it('returns nothing for an empty org, so the caller creates one', () => {
    expect(selectOnboardingProject([], 20)).toBeUndefined()
  })
})
