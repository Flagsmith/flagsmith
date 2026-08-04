import { ProjectFlag, Tag } from 'common/types/responses'

export const DEMO_FLAG_NAME = 'show_demo_button'

export const ONBOARDING_TAG = {
  color: '#3cb371',
  description: 'Created during onboarding',
  label: 'Onboarding',
}

// The demo flag from a previous run: tagged first, since the user is free to
// rename it, and a rename is a delete and recreate so the name alone is not
// reliable.
export const findDemoFlag = (
  flags: ProjectFlag[],
  onboardingTag?: Tag,
): ProjectFlag | undefined =>
  (onboardingTag && flags.find((f) => f.tags?.includes(onboardingTag.id))) ||
  flags.find((f) => f.name === DEMO_FLAG_NAME)

// Only seed into an empty project. An established project's flag list belongs to
// the customer, and a flag they did not ask for turns up in every environment,
// production included, because features are project-level.
export const shouldSeedDemoFlag = (flags: ProjectFlag[]): boolean =>
  !flags.length
