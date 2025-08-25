import { useGetSegmentQuery } from 'common/services/useSegment'
import { StageActionBody, StageActionType } from 'common/types/responses'
import moment from 'moment'

type FlagActionDetailProps = {
  actionType: StageActionType
  actionBody: StageActionBody
  projectId: number
}

export const renderActionDetail = (
  actionType: StageActionType,
  actionBody: StageActionBody,
  segmentName?: string,
  currentSplit?: number,
) => {
  const actionPrefixText = actionBody.enabled ? 'Enable' : 'Disable'
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
    case StageActionType.PHASED_ROLLOUT: {
      const { increase_by, increase_every, initial_split } = actionBody
      return (
        <div>
          <div className='mb-1'>
            <b>{actionPrefixText}</b> flag with <b>phased rollout</b>.
          </div>
          {initial_split && (
            <div className='mb-1'>
              Initial split of <b>{initial_split}%</b>
            </div>
          )}
          {increase_by && increase_every && (
            <div className='mb-1'>
              Increase by <b>{increase_by}%</b> every{' '}
              <b>
                {moment
                  .duration(increase_every)
                  .humanize()
                  .replace(/(a |in )/g, '')}
                .
              </b>
            </div>
          )}
          {currentSplit && (
            <div className='mb-1'>
              Current split of <b>{currentSplit}%</b>
            </div>
          )}
        </div>
      )
    }
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

  return renderActionDetail(actionType, actionBody, segmentData?.name)
}

export default FlagActionDetail
