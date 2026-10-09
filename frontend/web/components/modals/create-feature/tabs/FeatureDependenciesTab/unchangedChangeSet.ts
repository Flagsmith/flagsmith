import { FeatureState } from 'common/types/responses'
import { Req } from 'common/types/requests'

type ChangeSetBody = NonNullable<
  Req['createEnvironmentChangeRequest']['change_sets']
>[number]

// Until #8449, the API refuses a change request with no changes, so it
// carries the feature's current value unchanged. If the value changes before
// this is published, publishing puts the old one back; the page flags it as a
// conflict.
export const unchangedChangeSet = (
  featureId: number,
  featureStates: FeatureState[],
  liveFrom: string | undefined,
): ChangeSetBody | undefined => {
  const current = featureStates.find(
    (state) => !state.feature_segment && !state.identity,
  )
  if (!current) return
  const { id: _id, multivariate_feature_state_values, ...state } = current
  return {
    feature: featureId,
    feature_states_to_create: [],
    feature_states_to_update: [
      {
        ...state,
        multivariate_feature_state_values:
          multivariate_feature_state_values?.map(
            ({ id: _valueId, ...value }) => value,
          ),
      },
    ],
    live_from: liveFrom ?? new Date().toISOString(),
    segment_ids_to_delete_overrides: [],
  }
}
