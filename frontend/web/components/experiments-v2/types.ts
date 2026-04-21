// =============================================================================
// Experiments V2 — Types & Mock Data
// =============================================================================

// -----------------------------------------------------------------------------
// Enums & Primitives
// -----------------------------------------------------------------------------

export type ExperimentStatus = 'running' | 'paused' | 'completed' | 'draft'

export type WizardStepStatus = 'done' | 'active' | 'upcoming'

export type MetricRole = 'primary' | 'secondary' | 'guardrail'

export type LiftDirection = 'positive' | 'negative' | 'neutral'

/** Mock total identity count for the current environment, used to express
 *  each segment's share as a percentage of the environment. */
export const MOCK_ENVIRONMENT_USER_COUNT = 100000

// -----------------------------------------------------------------------------
// Wizard State
// -----------------------------------------------------------------------------

export type ExperimentDetails = {
  name: string
  hypothesis: string
  startDate: string
  endDate: string
}

export type MeasurementType = 'count' | 'occurrence' | 'value'
export type MetricDirection = 'higher-better' | 'lower-better' | 'neither'

export type Metric = {
  id: string
  name: string
  description: string
  role: MetricRole
  measurementType: MeasurementType
  direction: MetricDirection
  usageCount: number
  lastUpdated: string
}

export type Variation = {
  id: string
  name: string
  description: string
  value: string
  colour: string
}

/** Sentinel armId used for the implicit control arm in weight maps. */
export const CONTROL_ARM_ID = '__control__'

export type ArmWeight = {
  /** CONTROL_ARM_ID for control, otherwise a variation id. */
  armId: string
  weight: number
}

export type SegmentTrafficConfig = {
  segmentId: string | null
  /** Per-arm weights for users matched by the segment. Must sum to 100. */
  weights: ArmWeight[]
}

export type ExistingSegmentOverride = {
  segmentId: string
  segmentLabel: string
  priority: number
  weights: ArmWeight[]
}

export type ExperimentWizardState = {
  currentStep: number
  details: ExperimentDetails
  metrics: Metric[]
  featureFlagId: string | null
  controlValue: string
  variations: Variation[]
  segmentTraffic: SegmentTrafficConfig
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
  liftValue: number
  liftDirection: LiftDirection
  significance: string
  isSignificant: boolean
}

export type MetricTrendPoint = {
  day: number
  control: number
  treatment: number
}

export type MetricTrend = {
  metricName: string
  unit: '%' | '$' | 's'
  data: MetricTrendPoint[]
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
  metricTrends: MetricTrend[]
}

// -----------------------------------------------------------------------------
// Experiments List / Table
// -----------------------------------------------------------------------------

export type ExperimentListItem = {
  id: string
  name: string
  linkedFlag: string
  status: ExperimentStatus
  variations: number
  primaryMetric: string
  lastUpdated: string
}

export const MOCK_EXPERIMENTS: ExperimentListItem[] = [
  {
    id: 'exp-1',
    lastUpdated: '2 hours ago',
    linkedFlag: 'checkout_redesign',
    name: 'Checkout Flow v2',
    primaryMetric: 'Checkout Conversion',
    status: 'running',
    variations: 2,
  },
  {
    id: 'exp-2',
    lastUpdated: '1 day ago',
    linkedFlag: 'pricing_cta_test',
    name: 'Pricing Page CTA',
    primaryMetric: 'Revenue per User',
    status: 'paused',
    variations: 3,
  },
  {
    id: 'exp-3',
    lastUpdated: '3 days ago',
    linkedFlag: 'onboard_wizard_v3',
    name: 'Onboarding Wizard',
    primaryMetric: 'Signup Completion',
    status: 'completed',
    variations: 2,
  },
  {
    id: 'exp-4',
    lastUpdated: '5 days ago',
    linkedFlag: 'search_algo_v2',
    name: 'Search Algorithm',
    primaryMetric: 'Click-through Rate',
    status: 'running',
    variations: 3,
  },
  {
    id: 'exp-5',
    lastUpdated: '1 week ago',
    linkedFlag: 'dark_mode_flag',
    name: 'Dark Mode Default',
    primaryMetric: 'Page Load Time',
    status: 'draft',
    variations: 2,
  },
  {
    id: 'exp-6',
    lastUpdated: '2 weeks ago',
    linkedFlag: 'notif_timing',
    name: 'Notification Timing',
    primaryMetric: 'Open Rate',
    status: 'completed',
    variations: 2,
  },
  {
    id: 'exp-7',
    lastUpdated: '3 weeks ago',
    linkedFlag: 'trial_banner_exp',
    name: 'Free Trial Banner',
    primaryMetric: 'Trial Conversion',
    status: 'completed',
    variations: 2,
  },
]

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
  // The flag's base value. In Flagsmith's model, control is a single field
  // on the flag, not an entry in the variations list.
  controlValue: string
  // Additional values the flag splits across. Experiments compare these
  // against the control value.
  variations: Variation[]
  // Environment default weights for this flag. When no segment override
  // matches, identities hit these weights.
  envDefaultWeights: ArmWeight[]
  // Existing segment overrides already configured on this flag. An experiment
  // adds another override on top of these — priority order matters.
  existingSegmentOverrides: ExistingSegmentOverride[]
}

export type SegmentOption = {
  value: string
  label: string
  description?: string
  estimatedUsers: number
}

// =============================================================================
// Mock Data
// =============================================================================

export const MOCK_METRICS: Metric[] = [
  {
    description: 'Percentage of users completing checkout',
    direction: 'higher-better',
    id: 'met-1',
    lastUpdated: '2 days ago',
    measurementType: 'occurrence',
    name: 'Checkout Conversion Rate',
    role: 'primary',
    usageCount: 3,
  },
  {
    description: 'Average revenue generated per user session',
    direction: 'higher-better',
    id: 'met-2',
    lastUpdated: '1 week ago',
    measurementType: 'value',
    name: 'Revenue per User',
    role: 'secondary',
    usageCount: 5,
  },
  {
    description: 'Average page load time in milliseconds',
    direction: 'lower-better',
    id: 'met-3',
    lastUpdated: '3 days ago',
    measurementType: 'value',
    name: 'Page Load Time',
    role: 'secondary',
    usageCount: 2,
  },
  {
    description: 'Percentage of users who abandon the checkout flow',
    direction: 'lower-better',
    id: 'met-4',
    lastUpdated: '2 weeks ago',
    measurementType: 'occurrence',
    name: 'Cart Abandonment Rate',
    role: 'secondary',
    usageCount: 1,
  },
  {
    description: 'Average time users spend in a single session',
    direction: 'higher-better',
    id: 'met-5',
    lastUpdated: '1 month ago',
    measurementType: 'value',
    name: 'Session Duration',
    role: 'secondary',
    usageCount: 0,
  },
]

export const MOCK_VARIATIONS: Variation[] = [
  {
    colour: 'var(--purple-500)',
    description:
      'New checkout button with updated styling and CTA copy for improved conversion',
    id: 'var-2',
    name: 'Treatment B',
    value: 'false',
  },
]

const MOCK_SEARCH_VARIATIONS: Variation[] = [
  {
    colour: 'var(--purple-500)',
    description: 'ML-ranked results with personalised signals',
    id: 'var-search-2',
    name: 'Treatment B',
    value: 'v2',
  },
  {
    colour: 'var(--orange-500)',
    description: 'Hybrid ranker combining popularity and personalisation',
    id: 'var-search-3',
    name: 'Treatment C',
    value: 'v3',
  },
]

export const MOCK_FLAGS: FlagOption[] = [
  {
    controlValue: 'true',
    envDefaultWeights: [
      { armId: CONTROL_ARM_ID, weight: 100 },
      { armId: 'var-2', weight: 0 },
    ],
    existingSegmentOverrides: [
      {
        priority: 1,
        segmentId: 'seg-3',
        segmentLabel: 'Premium Tier',
        weights: [
          { armId: CONTROL_ARM_ID, weight: 0 },
          { armId: 'var-2', weight: 100 },
        ],
      },
    ],
    isMultiVariant: true,
    label: 'checkout_button_redesign',
    value: 'flag-1',
    variations: MOCK_VARIATIONS,
  },
  {
    controlValue: 'false',
    envDefaultWeights: [{ armId: CONTROL_ARM_ID, weight: 100 }],
    existingSegmentOverrides: [],
    isMultiVariant: false,
    label: 'new_pricing_page',
    value: 'flag-2',
    variations: [],
  },
  {
    controlValue: 'v1',
    envDefaultWeights: [
      { armId: CONTROL_ARM_ID, weight: 100 },
      { armId: 'var-search-2', weight: 0 },
      { armId: 'var-search-3', weight: 0 },
    ],
    existingSegmentOverrides: [],
    isMultiVariant: true,
    label: 'search_algorithm_v2',
    value: 'flag-3',
    variations: MOCK_SEARCH_VARIATIONS,
  },
  {
    controlValue: 'false',
    envDefaultWeights: [{ armId: CONTROL_ARM_ID, weight: 100 }],
    existingSegmentOverrides: [],
    isMultiVariant: false,
    label: 'onboarding_flow',
    value: 'flag-4',
    variations: [],
  },
  {
    controlValue: 'current',
    envDefaultWeights: [{ armId: CONTROL_ARM_ID, weight: 100 }],
    existingSegmentOverrides: [],
    isMultiVariant: true,
    label: 'homepage_hero_redesign',
    value: 'flag-5',
    variations: [],
  },
]

export const CONTROL_COLOUR = 'var(--green-500)'
export const MIN_VARIATIONS_FOR_EXPERIMENT = 1

export const MOCK_SEGMENTS: SegmentOption[] = [
  {
    description: 'Users accessing the product from a mobile device',
    estimatedUsers: 48000,
    label: 'Mobile Users',
    value: 'seg-2',
  },
  {
    description: 'Accounts on the Premium plan',
    estimatedUsers: 12000,
    label: 'Premium Tier',
    value: 'seg-3',
  },
  {
    description: 'Opt-in early access testers',
    estimatedUsers: 3200,
    label: 'Beta Testers',
    value: 'seg-4',
  },
]

const seedNoise = (seed: number): number => {
  const x = Math.sin(seed * 12.9898 + 78.233) * 43758.5453
  return x - Math.floor(x)
}

const buildSeries = (
  baseControl: number,
  baseTreatment: number,
  variance: number,
  precision: number,
  days: number,
  offset: number,
): MetricTrendPoint[] =>
  Array.from({ length: days }, (_, i) => {
    const controlNoise = (seedNoise(i + offset) - 0.5) * 2 * variance
    const treatmentNoise = (seedNoise(i + offset + 500) - 0.5) * 2 * variance
    const round = (v: number) =>
      Math.round(v * 10 ** precision) / 10 ** precision
    return {
      control: round(baseControl + baseControl * controlNoise),
      day: i + 1,
      treatment: round(baseTreatment + baseTreatment * treatmentNoise),
    }
  })

const buildMockTrends = (): MetricTrend[] => [
  {
    data: buildSeries(7.2, 8.3, 0.08, 2, 23, 10),
    metricName: 'Conversion Rate',
    unit: '%',
  },
  {
    data: buildSeries(24.1, 27.5, 0.07, 2, 23, 20),
    metricName: 'Revenue per User',
    unit: '$',
  },
  {
    data: buildSeries(2.4, 2.3, 0.05, 2, 23, 30),
    metricName: 'Page Load Time',
    unit: 's',
  },
]

export const MOCK_EXPERIMENT_RESULT: ExperimentResultSummary = {
  daysCurrent: 23,
  daysTotal: 30,
  id: 'exp-1',
  lastUpdated: '2 min ago',
  liftVsControl: 18.3,
  metricTrends: buildMockTrends(),
  metrics: [
    {
      control: '7.2%',
      isSignificant: true,
      lift: '+15.3%',
      liftDirection: 'positive',
      liftValue: 15.3,
      name: 'Conversion Rate',
      significance: 'p<0.01',
      treatment: '8.3%',
    },
    {
      control: '$24.10',
      isSignificant: true,
      lift: '+14.1%',
      liftDirection: 'positive',
      liftValue: 14.1,
      name: 'Revenue per User',
      significance: 'p<0.05',
      treatment: '$27.50',
    },
    {
      control: '2.4s',
      isSignificant: false,
      lift: '-4.2%',
      liftDirection: 'neutral',
      liftValue: -4.2,
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
    subtitle: 'Name your experiment and describe your hypothesis',
    title: 'Experiment Details',
  },
  {
    subtitle: 'Select the multi-variant flag to experiment on',
    title: 'Flag & Variations',
  },
  {
    subtitle: 'Choose primary and secondary metrics to measure',
    title: 'Select Metrics',
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
