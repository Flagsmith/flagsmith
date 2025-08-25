import moment from 'moment'

import {
  Features,
  StageAction,
  StageTrigger,
  StageTriggerType,
} from 'common/types/responses'

import Icon from 'components/Icon'

import { renderActionDetail } from './FlagActionDetail'

export interface StageSummaryDataProps {
  stageActions?: StageAction[]
  stageTrigger?: StageTrigger
  featureInStage?: Features[number]
}

const StageSummaryData = ({
  featureInStage,
  stageActions,
  stageTrigger,
}: StageSummaryDataProps) => {
  const isWaitType = stageTrigger?.trigger_type === StageTriggerType.WAIT_FOR

  const waitForTimeoutDuration = moment.duration(
    stageTrigger?.trigger_body?.wait_for,
  )

  const timeDifference = featureInStage?.created_at
    ? moment().diff(moment(featureInStage.created_at))
    : 0

  const timeoutDuration =
    featureInStage?.created_at && stageTrigger?.trigger_body?.wait_for
      ? waitForTimeoutDuration.asMilliseconds()
      : 0

  const timeRemaining = timeoutDuration - timeDifference
  const timeRemainingDuration = moment.duration(Math.max(0, timeRemaining))

  const isTimeLeft = timeRemainingDuration.asMilliseconds() > 0
  const isTimePending = isWaitType && isTimeLeft

  return (
    <div className='p-2'>
      <h6>Status</h6>
      {isWaitType && (
        <div>
          <Row>
            <Icon
              name={isTimeLeft ? 'timer' : 'checkmark-circle'}
              width={18}
              height={18}
              fill={isTimeLeft ? '#6837FC' : '#53af41'}
            />
            <div className='ml-2'>
              Wait for {waitForTimeoutDuration.humanize()} to proceed to next
              action
            </div>
          </Row>
          {isTimeLeft && (
            <div className='text-muted ml-4 mt-1'>
              {moment.duration(timeRemainingDuration).humanize()} remaining
            </div>
          )}
        </div>
      )}

      {stageActions?.map((action) => (
        <Row key={action.id} className='mt-2 align-items-start'>
          <div>
            <Icon
              name={isTimePending ? 'radio' : 'checkmark-circle'}
              width={18}
              height={18}
              fill={isTimePending ? '#767d85' : '#53af41'}
            />
          </div>
          <div className='ml-2'>
            {renderActionDetail(
              action.action_type,
              action.action_body,
              '',
              featureInStage?.phased_rollout_state?.current_split,
            )}
          </div>
        </Row>
      ))}
    </div>
  )
}

export default StageSummaryData
