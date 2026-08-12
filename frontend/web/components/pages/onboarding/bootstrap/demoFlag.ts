import { ProjectFlag, Tag } from 'common/types/responses'

export const DEMO_FLAG_NAME = 'show_demo_button'

export const ONBOARDING_TAG = {
  color: '#3cb371',
  description: 'Created during onboarding',
  label: 'Onboarding',
}

// Description too: a customer's own tag labelled Onboarding is not ours.
export const findOnboardingTag = (tags: Tag[]): Tag | undefined =>
  tags.find(
    (t) =>
      t.label === ONBOARDING_TAG.label &&
      t.description === ONBOARDING_TAG.description,
  )

// A previous run's flag. Tag first: renaming is a delete and recreate, so the
// name alone is not reliable.
export const findDemoFlag = (
  flags: ProjectFlag[],
  onboardingTag?: Tag,
): ProjectFlag | undefined =>
  (onboardingTag && flags.find((f) => f.tags?.includes(onboardingTag.id))) ||
  flags.find((f) => f.name === DEMO_FLAG_NAME)

// Only seed into an empty project: features are project-level, so an unwanted
// flag shows up in every environment, production included.
export const shouldSeedDemoFlag = (flags: ProjectFlag[]): boolean =>
  !flags.length

// The tour toggles and renames what it finds, so only carry on while ours is
// the only flag here. One flag is also what a mid-tour refresh finds.
export const canResumeDemoFlag = (
  flags: ProjectFlag[],
  flag: ProjectFlag,
): boolean => flags.length === 1 && flags[0].id === flag.id
