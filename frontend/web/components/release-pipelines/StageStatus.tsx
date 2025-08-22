import ProjectStore from 'common/stores/project-store'
import {
  Environment,
  Features,
  StageAction,
  StageTrigger,
  StageTriggerType,
} from 'common/types/responses'
import classNames from 'classnames'
import Icon from 'components/Icon'
import { renderToString } from 'react-dom/server'

import StageSummaryData from './StageSummaryData'

export interface StageStatusProps {
  stageOrder: number
  stageName: string
  totalStages: number
  stageActions?: StageAction[]
  stageTrigger?: StageTrigger
  stageEnvironment?: number
  featureInStage?: Features[number]
  isCompleted?: boolean
}

const StageStatus = ({
  featureInStage,
  isCompleted,
  stageActions,
  stageEnvironment,
  stageName,
  stageOrder,
  stageTrigger,
  totalStages,
}: StageStatusProps) => {
  const isFeatureInStage = !!featureInStage
  const showLine = totalStages > 1
  const lastStage = stageOrder === totalStages - 1
  const showLeftLine = showLine && stageOrder > 0
  const showRightLine = showLine && stageOrder !== totalStages - 1

  const isWaiting =
    stageTrigger?.trigger_type === StageTriggerType.WAIT_FOR && isFeatureInStage
  const isLastStage = stageOrder === totalStages - 1

  const stageStyle = {
    marginRight: lastStage ? '0px' : '24px',
  }

  const env = ProjectStore.getEnvironmentById(
    stageEnvironment,
  ) as unknown as Environment
  const envName = env?.name

  return (
    <div
      className='flex align-items-center gap-2 position-relative flex-1'
      style={stageStyle}
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
            className={classNames('circle-container', {
              'completed': isCompleted,
              'in-stage': isFeatureInStage,
            })}
          >
            {isWaiting ? (
              <Icon name='timer' width={18} height={18} fill='#6837FC' />
            ) : undefined}
            {isCompleted ? (
              <Icon
                name='checkmark-circle'
                width={18}
                height={18}
                fill='#53af41'
              />
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
              />,
            )}
      </Tooltip>
      <span>
        <b>{stageName}</b>
      </span>
      {envName && <p className='text-muted'>{envName}</p>}
    </div>
  )
}

export default StageStatus
