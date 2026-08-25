import type { FeatureStateValue, FlagsmithValue } from 'common/types/responses'

/**
 * Flattens a feature state (or core trait) value into its typed scalar.
 *
 * Accepts either the nested `{ type, string_value, ... }` shape returned by the
 * featurestates endpoint or an already-flat value, and returns the flat value.
 *
 * Kept in its own module, free of `common/utils` imports, so consumers (and
 * their unit tests) don't pull the Flux stores in through `utils.tsx`.
 */
export function featureStateToValue(
  value: FlagsmithValue | FeatureStateValue | undefined,
): FlagsmithValue {
  if (value === null || value === undefined) {
    return null
  }
  if (typeof value !== 'object') {
    return value
  }
  // `value_type` is the type key on core traits; `type` on feature states.
  const type =
    (value as { value_type?: FeatureStateValue['type'] }).value_type ??
    value.type
  switch (type) {
    case 'bool':
      return value.boolean_value
    case 'float':
      return value.float_value ?? null
    case 'int':
      return value.integer_value ?? null
    default:
      return value.string_value
  }
}
