import { ProjectFlag, Tag } from 'common/types/responses'

export const DEMO_FLAG_NAME = 'show_demo_button'

// Set on the flag we create, and carried over by the tour's rename, so it
// identifies our flag after the name has changed. Also tells anyone looking at
// their flag list why it is there.
export const DEMO_FLAG_DESCRIPTION = 'Created during onboarding'

export const ONBOARDING_TAG = {
  color: '#3cb371',
  description: DEMO_FLAG_DESCRIPTION,
  label: 'Onboarding',
}

// Description too: a customer's own tag labelled Onboarding is not ours.
export const findOnboardingTag = (tags: Tag[]): Tag | undefined =>
  tags.find(
    (t) =>
      t.label === ONBOARDING_TAG.label &&
      t.description === ONBOARDING_TAG.description,
  )

// Our flag, in descending order of how much the signal is worth. The tour
// renames by delete and recreate, carrying the tags and description over, so
// the name is the one thing that doesn't survive it: it only identifies flags
// seeded before we set a description.
export const findDemoFlag = (
  flags: ProjectFlag[],
  onboardingTag?: Tag,
): ProjectFlag | undefined =>
  (onboardingTag && flags.find((f) => f.tags?.includes(onboardingTag.id))) ||
  flags.find((f) => f.description === DEMO_FLAG_DESCRIPTION) ||
  flags.find((f) => f.name === DEMO_FLAG_NAME)
