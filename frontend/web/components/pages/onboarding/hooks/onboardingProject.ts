import { ProjectSummary } from 'common/types/responses'

// /getting-started is an entry point rather than a project-scoped page, so the
// project it should run against arrives as `?project=`. The URL is authoritative:
// an id that isn't in this organisation's list is ignored rather than trusted.
export const selectOnboardingProject = (
  projects: ProjectSummary[],
  requestedProjectId?: string | number | null,
): ProjectSummary | undefined => {
  const requested =
    !!requestedProjectId &&
    projects.find((p) => `${p.id}` === `${requestedProjectId}`)
  return requested || projects[0]
}
