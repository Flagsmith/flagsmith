import { ChangeSet, FeatureState } from 'common/types/responses'

type FeatureSource = {
  feature_states: Pick<FeatureState, 'feature'>[]
  change_sets?: Pick<ChangeSet, 'feature'>[]
}

export const getChangeRequestFeature = (
  changeRequest: FeatureSource | undefined,
): number | undefined =>
  changeRequest?.feature_states[0]?.feature ||
  changeRequest?.change_sets?.[0]?.feature
