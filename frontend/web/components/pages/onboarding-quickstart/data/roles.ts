export type OnboardingRoleKey = 'engineer' | 'pm' | 'other'

export type OnboardingRole = {
  key: OnboardingRoleKey
  title: string
  // Short (3–5 word) description of what this path focuses on, shown on the
  // role button so the choice is concrete rather than vague.
  focus: string
}

export const ONBOARDING_ROLES: OnboardingRole[] = [
  { focus: 'Get the SDK working', key: 'engineer', title: 'Engineer' },
  { focus: 'Manage flags, no code', key: 'pm', title: 'Product manager' },
  { focus: 'Explore the dashboard', key: 'other', title: 'Other' },
]
