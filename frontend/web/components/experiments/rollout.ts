import {
  FlagsmithValue,
  MultivariateOption,
  ProjectFlag,
} from 'common/types/responses'
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

export const buildRolloutSummary = (
  rolloutPercentage: number,
  rows: RolloutSummaryRow[],
): string =>
  `${rolloutPercentage}% of eligible identities enter the experiment. Split: ${rows
    .map((row) => `${row.label} ${row.percentage}%`)
    .join(', ')}.`
