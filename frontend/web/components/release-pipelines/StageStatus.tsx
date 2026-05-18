import {
  Features,
  StageAction,
  StageTrigger,
  StageTriggerType,
} from 'common/types/responses'
import classNames from 'classnames'
import Icon from 'components/icons/Icon'
import { renderToString } from 'react-dom/server'

import StageSummaryData from './StageSummaryData'

interface StageStatusProps {
  stageOrder: number
  stageName: string
  totalStages: number
  stageActions?: StageAction[]
  stageTrigger?: StageTrigger
  envName?: string
  featureInStage?: Features[number]
  isCompleted?: boolean
}

const StageStatus = ({
  envName,
  featureInStage,
  isCompleted,
  stageActions,
  stageName,
  stageOrder,
  stageTrigger,
  totalStages,
}: StageStatusProps) => {
  const isFeatureInStage = !!featureInStage
  const showLine = totalStages > 1
  const isLastStage = stageOrder === totalStages - 1
  const showLeftLine = showLine && stageOrder > 0
  const showRightLine = showLine && !isLastStage

  const isWaiting =
    stageTrigger?.trigger_type === StageTriggerType.WAIT_FOR && isFeatureInStage

  return (
    <div
      className={classNames(
        'flex align-items-center gap-2 position-relative flex-1',
        isLastStage ? 'me-0' : 'me-4',
      )}
    >
      {showLeftLine && (
        <div
          className={classNames('position-absolute line-left', {
            'completed': isCompleted || isFeatureInStage,
          })}
        />
      )}
      {showRightLine && (
        <div
          className={classNames('position-absolute line-right', {
            'completed': isCompleted,
          })}
        />
      )}
      <Tooltip
        titleClassName='circle-container-z-index'
        title={
          <div
            className={classNames('circle-container cursor-pointer', {
              'completed': isCompleted,
              'in-stage': isFeatureInStage,
            })}
          >
            {isWaiting ? (
              <Icon name='timer' width={18} height={18} />
            ) : undefined}
            {isCompleted ? (
              <Icon name='checkmark-circle' width={18} height={18} />
            ) : undefined}
          </div>
        }
      >
        {isLastStage
          ? ''
          : renderToString(
              <StageSummaryData
                stageActions={stageActions}
                stageTrigger={stageTrigger}
                featureInStage={featureInStage}
                isCompleted={isCompleted}
              />,
            )}
      </Tooltip>
      <span>
        <b>{stageName}</b>
      </span>
      {envName && <span className='text-muted'>{envName}</span>}
    </div>
  )
}

export default StageStatus
