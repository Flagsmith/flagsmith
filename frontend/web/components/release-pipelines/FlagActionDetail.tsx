import { useGetSegmentQuery } from 'common/services/useSegment'
import { StageActionBody, StageActionType } from 'common/types/responses'

type FlagActionDetailProps = {
  actionType: StageActionType
  actionBody: StageActionBody
  projectId: number
}

const FlagActionDetail = ({
  actionBody,
  actionType,
  projectId,
}: FlagActionDetailProps) => {
  const { data: segmentData, isLoading: isSegmentLoading } = useGetSegmentQuery(
    {
      id: `${actionBody.segment_id}`,
      projectId: `${projectId}`,
    },
    {
      skip:
        !actionBody.segment_id ||
        actionType !== StageActionType.TOGGLE_FEATURE_FOR_SEGMENT,
    },
  )

  if (isSegmentLoading) {
    return null
  }

  if (
    actionType === StageActionType.TOGGLE_FEATURE_FOR_SEGMENT &&
    actionBody.segment_id
  ) {
    return (
      <span>
        Enable flag for a segment: <b>{segmentData?.name}</b>
      </span>
    )
  }

  if (actionType === StageActionType.TOGGLE_FEATURE) {
    return (
      <span>
        Disable flag for <b>everyone</b>
      </span>
    )
  }

  return null
}

export default FlagActionDetail
