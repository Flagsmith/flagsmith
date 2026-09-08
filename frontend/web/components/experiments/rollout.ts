import {
  ExperimentAudienceMatch,
  FlagsmithValue,
  MultivariateOption,
  ProjectFlag,
  SegmentCohort,
} from 'common/types/responses'
import {
  ExperimentAudienceBody,
  ExperimentRolloutBody,
} from 'common/types/requests'
import { getDefaultVariantKey } from 'common/utils/multivariate'
import {
  CHART_COLOURS,
  colorTextAction,
  colorTextSuccess,
} from 'common/theme/tokens'

export type VariationSplitEntry = {
  multivariate_feature_option: number
  percentage_allocation: number
}

export type RolloutFeatureValue = {
  type: 'integer' | 'string' | 'boolean'
  value: string
}

export const toRolloutFeatureValue = (
  value: FlagsmithValue,
): RolloutFeatureValue => {
  if (typeof value === 'boolean') {
    return { type: 'boolean', value: value ? 'true' : 'false' }
  }
  if (typeof value === 'number') {
    return { type: 'integer', value: String(value) }
  }
  return { type: 'string', value: value ?? '' }
}

export type RolloutSummaryRow = {
  label: string
  percentage: number
}

export const CONTROL_COLOUR = colorTextSuccess
export const VARIATION_COLOURS = [colorTextAction, ...CHART_COLOURS]

export const getVariationColour = (index: number): string =>
  VARIATION_COLOURS[index % VARIATION_COLOURS.length]

export const getVariationSplitDefaults = (
  options: MultivariateOption[],
  environmentValues: VariationSplitEntry[] = [],
): VariationSplitEntry[] =>
  options.map((option) => {
    const override = environmentValues.find(
      (value) => value.multivariate_feature_option === option.id,
    )
    return {
      multivariate_feature_option: option.id,
      percentage_allocation:
        override?.percentage_allocation ||
        option.default_percentage_allocation ||
        0,
    }
  })

export const getEvenSplit = (
  options: MultivariateOption[],
): VariationSplitEntry[] => {
  const slots = options.length + 1
  const base = Math.floor(100 / slots)
  const remainder = 100 - base * slots
  return options.map((option, index) => ({
    multivariate_feature_option: option.id,
    percentage_allocation: base + (index + 1 < remainder ? 1 : 0),
  }))
}

export const getControlPercentage = (
  variationSplit: VariationSplitEntry[],
): number =>
  100 -
  variationSplit.reduce(
    (total, entry) => total + (entry.percentage_allocation || 0),
    0,
  )

export const getRolloutSummaryRows = (
  feature: ProjectFlag,
  variationSplit: VariationSplitEntry[],
): RolloutSummaryRow[] => [
  {
    label: 'Control',
    percentage: Math.max(0, getControlPercentage(variationSplit)),
  },
  ...feature.multivariate_options.map((option, index) => ({
    label: option.key || getDefaultVariantKey(index),
    percentage:
      variationSplit.find(
        (entry) => entry.multivariate_feature_option === option.id,
      )?.percentage_allocation ?? 0,
  })),
]

export type TrafficSegment = {
  label: string
  percentage: number
  colour: string
}

export const getTrafficSegments = (
  feature: ProjectFlag,
  variationSplit: VariationSplitEntry[],
  rolloutPercentage: number,
): TrafficSegment[] =>
  getRolloutSummaryRows(feature, variationSplit).map((row, index) => ({
    colour: index === 0 ? CONTROL_COLOUR : getVariationColour(index - 1),
    label: row.label,
    percentage: (rolloutPercentage * row.percentage) / 100,
  }))

// Matches the API cap, held at one until the Java SDK respects sub-rule types.
export const MAX_AUDIENCE_SEGMENTS = 1

// The subset of a segment the wizard keeps once it has been picked.
export type AudienceSegment = {
  id: number
  name: string
  cohort?: SegmentCohort | null
  description?: string
  membershipCount?: number
}

export type RolloutAudience = {
  match: ExperimentAudienceMatch
  segments: { name: string }[]
}

export const joinSegmentNames = (names: string[], joiner: string): string =>
  names.length < 2
    ? names.join('')
    : `${names.slice(0, -1).join(', ')} ${joiner} ${names[names.length - 1]}`

export const buildAudienceDescription = (
  audience?: RolloutAudience,
): string => {
  const names = audience?.segments.map((segment) => segment.name) ?? []
  if (!names.length) return 'eligible identities'
  return `identities in ${joinSegmentNames(
    names,
    audience?.match === 'all' ? 'and' : 'or',
  )}`
}

export const buildRolloutSummary = (
  rolloutPercentage: number,
  rows: RolloutSummaryRow[],
  audience?: RolloutAudience,
): string =>
  `${rolloutPercentage}% of ${buildAudienceDescription(
    audience,
  )} enter the experiment. Split: ${rows
    .map((row) => `${row.label} ${row.percentage}%`)
    .join(', ')}.`

export const toAudiencePayload = (
  segments: AudienceSegment[],
  match: ExperimentAudienceMatch,
): ExperimentAudienceBody | undefined =>
  segments.length
    ? { match, segment_ids: segments.map((segment) => segment.id) }
    : undefined

// The single place the rollout request body is shaped, so the wizard and the
// detail-page editor agree on it. An absent audience leaves the key off
// entirely, since the API reads a present `audience` as a replacement.
export const buildRolloutBody = ({
  audience,
  enabled,
  featureStateValue,
  rolloutPercentage,
  variationSplit,
}: {
  enabled: boolean
  rolloutPercentage: number
  featureStateValue: RolloutFeatureValue
  variationSplit: VariationSplitEntry[]
  audience?: ExperimentAudienceBody
}): ExperimentRolloutBody => {
  const body: ExperimentRolloutBody = {
    enabled,
    feature_state_value: featureStateValue,
    multivariate_feature_state_values: variationSplit,
    rollout_percentage: rolloutPercentage,
  }
  return audience ? { ...body, audience } : body
}
