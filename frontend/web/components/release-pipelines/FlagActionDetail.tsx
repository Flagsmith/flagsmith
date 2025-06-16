import { useGetSegmentQuery } from 'common/services/useSegment'
import { StageActionBody, StageActionType } from 'common/types/responses'

type FlagActionDetailProps = {
  actionType: StageActionType
  actionBody: StageActionBody
  projectId: number
}

const renderActionDetail = (
  actionType: StageActionType,
  enabled: boolean,
  segmentName?: string,
) => {
  const actionPrefixText = enabled ? 'Enable' : 'Disable'
  switch (actionType) {
    case StageActionType.TOGGLE_FEATURE_FOR_SEGMENT:
      return (
        <span>
          {actionPrefixText} flag for segment <b>{segmentName}</b>
        </span>
      )
    case StageActionType.TOGGLE_FEATURE:
      return (
        <span>
          {actionPrefixText} flag for <b>everyone</b>
        </span>
      )
    default:
      return null
  }
}

const FlagActionDetail = ({
  actionBody,
  actionType,
  projectId,
}: FlagActionDetailProps) => {
  const isSegmentAction =
    actionType === StageActionType.TOGGLE_FEATURE_FOR_SEGMENT
  const { data: segmentData } = useGetSegmentQuery(
    {
      id: `${actionBody.segment_id}`,
      projectId: `${projectId}`,
    },
    {
      skip: !actionBody.segment_id || !isSegmentAction,
    },
  )

  return renderActionDetail(actionType, actionBody.enabled, segmentData?.name)
}

export default FlagActionDetail
