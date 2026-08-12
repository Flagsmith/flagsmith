import { ProjectSummary } from 'common/types/responses'

// The project the user just made: creating one and clicking Getting Started is
// how you run onboarding again. The list comes back in no useful order, so go
// by id rather than position.
export const newestProject = (
  projects: ProjectSummary[],
): ProjectSummary | undefined =>
  projects.reduce<ProjectSummary | undefined>(
    (newest, project) => (!newest || project.id > newest.id ? project : newest),
    undefined,
  )
