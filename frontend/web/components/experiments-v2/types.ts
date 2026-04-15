// =============================================================================
// Experiments V2 — Types & Mock Data
// =============================================================================

// -----------------------------------------------------------------------------
// Enums & Primitives
// -----------------------------------------------------------------------------

export type ExperimentType = 'ab_test' | 'multivariate' | 'feature_flag'

export type ExperimentStatus = 'running' | 'paused' | 'completed'

export type WizardStepStatus = 'done' | 'active' | 'upcoming'

export type MetricRole = 'primary' | 'secondary'

export type LiftDirection = 'positive' | 'negative' | 'neutral'

// -----------------------------------------------------------------------------
// Wizard State
// -----------------------------------------------------------------------------

export type ExperimentDetails = {
  name: string
  hypothesis: string
  type: ExperimentType | null
  startDate: string
  endDate: string
}

export type Metric = {
  id: string
  name: string
  description: string
  role: MetricRole
}

export type Variation = {
  id: string
  name: string
  description: string
  value: string
  colour: string
}

export type TrafficSplit = {
  variationId: string
  percentage: number
}

export type AudienceConfig = {
  segmentId: string | null
  trafficPercentage: number
  splits: TrafficSplit[]
}

export type ExperimentWizardState = {
  currentStep: number
  details: ExperimentDetails
  metrics: Metric[]
  featureFlagId: string | null
  variations: Variation[]
  audience: AudienceConfig
}

// -----------------------------------------------------------------------------
// Wizard Step Definition (for sidebar)
// -----------------------------------------------------------------------------

export type WizardStepDef = {
  title: string
  subtitle: string
  completeSummary?: string
}

// -----------------------------------------------------------------------------
// Results Page
// -----------------------------------------------------------------------------

export type MetricComparison = {
  name: string
  control: string
  treatment: string
  lift: string
  liftDirection: LiftDirection
  significance: string
  isSignificant: boolean
}

export type ExperimentResultSummary = {
  id: string
  name: string
  status: ExperimentStatus
  daysCurrent: number
  daysTotal: number
  primaryMetric: string
  lastUpdated: string
  usersEnrolled: number
  winningVariation: string
  probabilityToBest: number
  liftVsControl: number
  metrics: MetricComparison[]
}

// -----------------------------------------------------------------------------
// Flag Detail — Linked Experiment
// -----------------------------------------------------------------------------

export type LinkedExperiment = {
  id: string
  name: string
  status: ExperimentStatus
  primaryMetric: string
  runningSince: string
  trafficSplit: string
  sampleProgress: number
  sampleTarget: number
}

// -----------------------------------------------------------------------------
// Dropdown Options
// -----------------------------------------------------------------------------

export type FlagOption = {
  value: string
  label: string
  // Experiments can only run on multi-variant flags — single-variant flags
  // are filtered out of the selector.
  isMultiVariant: boolean
}

export type SegmentOption = {
  value: string
  label: string
}

// =============================================================================
// Mock Data
// =============================================================================

export const MOCK_METRICS: Metric[] = [
  {
    description: 'Percentage of users completing checkout',
    id: 'met-1',
    name: 'Checkout Conversion Rate',
    role: 'primary',
  },
  {
    description: 'Average revenue generated per user session',
    id: 'met-2',
    name: 'Revenue per User',
    role: 'secondary',
  },
  {
    description: 'Average page load time in milliseconds',
    id: 'met-3',
    name: 'Page Load Time',
    role: 'secondary',
  },
  {
    description: 'Percentage of users who abandon the checkout flow',
    id: 'met-4',
    name: 'Cart Abandonment Rate',
    role: 'secondary',
  },
  {
    description: 'Average time users spend in a single session',
    id: 'met-5',
    name: 'Session Duration',
    role: 'secondary',
  },
]

export const MOCK_FLAGS: FlagOption[] = [
  { isMultiVariant: true, label: 'checkout_button_redesign', value: 'flag-1' },
  { isMultiVariant: false, label: 'new_pricing_page', value: 'flag-2' },
  { isMultiVariant: true, label: 'search_algorithm_v2', value: 'flag-3' },
  { isMultiVariant: false, label: 'onboarding_flow', value: 'flag-4' },
]

export const MOCK_SEGMENTS: SegmentOption[] = [
  { label: 'All Users', value: 'seg-1' },
  { label: 'Mobile Users', value: 'seg-2' },
  { label: 'Premium Tier', value: 'seg-3' },
]

export const MOCK_VARIATIONS: Variation[] = [
  {
    colour: 'var(--green-500)',
    description:
      'Original checkout button design — serves as the baseline for comparison',
    id: 'var-1',
    name: 'Control',
    value: 'true',
  },
  {
    colour: 'var(--purple-500)',
    description:
      'New checkout button with updated styling and CTA copy for improved conversion',
    id: 'var-2',
    name: 'Treatment B',
    value: 'false',
  },
]

export const MOCK_EXPERIMENT_RESULT: ExperimentResultSummary = {
  daysCurrent: 23,
  daysTotal: 30,
  id: 'exp-1',
  lastUpdated: '2 min ago',
  liftVsControl: 18.3,
  metrics: [
    {
      control: '7.2%',
      isSignificant: true,
      lift: '+15.3%',
      liftDirection: 'positive',
      name: 'Conversion Rate',
      significance: 'p<0.01',
      treatment: '8.3%',
    },
    {
      control: '$24.10',
      isSignificant: true,
      lift: '+14.1%',
      liftDirection: 'positive',
      name: 'Revenue per User',
      significance: 'p<0.05',
      treatment: '$27.50',
    },
    {
      control: '2.4s',
      isSignificant: false,
      lift: '-4.2%',
      liftDirection: 'neutral',
      name: 'Page Load Time',
      significance: 'not significant',
      treatment: '2.3s',
    },
  ],
  name: 'Checkout Button Redesign',
  primaryMetric: 'Conversion Rate',
  probabilityToBest: 94.2,
  status: 'running',
  usersEnrolled: 12847,
  winningVariation: 'Treatment B',
}

export const MOCK_LINKED_EXPERIMENT: LinkedExperiment = {
  id: 'exp-1',
  name: 'Checkout Button A/B Test',
  primaryMetric: 'Conversion Rate',
  runningSince: 'Mar 15, 2026  (23 days)',
  sampleProgress: 6800,
  sampleTarget: 10000,
  status: 'running',
  trafficSplit: '50% / 50%',
}

export const EXPERIMENT_WIZARD_STEPS: WizardStepDef[] = [
  {
    subtitle: 'Define the basics of your experiment',
    title: 'Experiment Details',
  },
  {
    subtitle: 'Choose primary and secondary metrics to measure',
    title: 'Select Metrics',
  },
  {
    subtitle: 'Configure your feature flag and test variations',
    title: 'Flag & Variations',
  },
  {
    subtitle: 'Define who sees the experiment and traffic allocation',
    title: 'Segments & Traffic',
  },
  {
    subtitle: 'Review your configuration and launch',
    title: 'Review & Launch',
  },
]
