export type OnboardingRoleKey = 'engineer' | 'pm' | 'other'

export type OnboardingRole = {
  key: OnboardingRoleKey
  title: string
}

export const ONBOARDING_ROLES: OnboardingRole[] = [
  { key: 'engineer', title: 'Engineer' },
  { key: 'pm', title: 'Product manager' },
  { key: 'other', title: 'Something else' },
]
