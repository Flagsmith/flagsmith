export type FeaturePreset = {
  key: string
  label: string
}

export const FEATURE_PRESETS: FeaturePreset[] = [
  {
    key: 'show_demo_button',
    label: 'show_demo_button — toggle a button in your UI',
  },
  {
    key: 'send_onboarding_email',
    label: 'send_onboarding_email — gate an email send',
  },
]

export const CONCEPT_ITEMS = [
  {
    description: 'Auto-ticked when you ran the snippet.',
    id: 'first-flag',
    title: 'Create your first flag',
  },
  {
    description: 'Get your team set up in Flagsmith.',
    id: 'invite-teammate',
    title: 'Invite a teammate',
  },
  {
    description: 'Use segments + identities to target a subset of users.',
    id: 'target-user',
    title: 'Target a specific user',
  },
  {
    description: 'Percentage rollouts to release gradually.',
    id: 'rollout',
    title: 'Roll out gradually',
  },
  {
    description: 'Use multiple environments to promote between them.',
    id: 'promote',
    title: 'Promote to production',
  },
] as const

export type ConceptItemId = (typeof CONCEPT_ITEMS)[number]['id']
