import type {
  FeatureStateValue,
  FlagsmithValue,
  MultivariateOption,
  TraitValue,
} from 'common/types/responses'

/**
 * Flattens a feature state (or core trait) value into its typed scalar.
 *
 * Accepts either the nested `{ type, string_value, ... }` shape returned by the
 * featurestates endpoint or an already-flat value, and returns the flat value.
 * Multivariate options carry that same nested shape, so they are accepted too.
 *
 * Kept in its own module, free of `common/utils` imports, so consumers (and
 * their unit tests) don't pull the Flux stores in through `utils.tsx`.
 */
export type FeatureStateToValueInput =
  | FlagsmithValue
  | FeatureStateValue
  | MultivariateOption
  | TraitValue
  | undefined

export function featureStateToValue(
  value: FeatureStateToValueInput,
): FlagsmithValue {
  if (value === null || value === undefined) {
    return null
  }
  if (typeof value !== 'object') {
    return value
  }
  // `value_type` is the type key on core traits; `type` on feature states.
  const type = 'value_type' in value ? value.value_type : value.type
  switch (type) {
    case 'bool':
      // Optional on multivariate options, so it can be absent.
      return value.boolean_value ?? null
    case 'float':
      // Only traits carry a float. Feature state values and variations do not.
      return 'float_value' in value ? value.float_value ?? null : null
    case 'int':
      return value.integer_value ?? null
    default:
      return value.string_value
  }
}
