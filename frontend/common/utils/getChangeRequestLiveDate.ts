import moment from 'moment/moment'
import { ChangeRequest } from 'common/types/responses'

export const getChangeRequestLiveDate = (
  changeRequest: ChangeRequest | null | undefined,
) => {
  if (!changeRequest) return null
  return changeRequest.environment_feature_versions.length > 0
    ? moment(changeRequest.environment_feature_versions?.[0]?.live_from)
    : changeRequest?.change_sets?.[0]?.live_from
    ? moment(changeRequest?.change_sets?.[0]?.live_from)
    : moment(changeRequest.feature_states?.[0]?.live_from)
}
