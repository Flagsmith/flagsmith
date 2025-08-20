import moment from 'moment'

import {
  useGetReleasePipelineQuery,
  useGetReleasePipelinesQuery,
} from 'common/services/useReleasePipelines'
import AccordionCard from 'components/base/accordion/AccordionCard'
import ProjectStore from 'common/stores/project-store'
import {
  Environment,
  Features,
  StageAction,
  StageTrigger,
  StageTriggerType,
} from 'common/types/responses'
import classNames from 'classnames'
import { useMemo } from 'react'
import Icon from 'components/Icon'
import { renderToString } from 'react-dom/server'

import { renderActionDetail } from './FlagActionDetail'

interface StageStatusProps {
  stageOrder: number
  stageName: string
  totalStages: number
  stageActions?: StageAction[]
  stageTrigger?: StageTrigger
  stageEnvironment?: number
  featureCurrentStageOrder?: number
  isCompleted?: boolean
}

const StageSummaryData = ({
  stageActions,
  stageTrigger,
}: {
  stageActions?: StageAction[]
  stageTrigger?: StageTrigger
  projectId?: number
}) => {
  const isWaitType = stageTrigger?.trigger_type === StageTriggerType.WAIT_FOR
  const isTimeoutCompleted = false
  const isActionPending = isWaitType && !isTimeoutCompleted

  return (
    <div>
      <h6>Status</h6>
      {isWaitType && (
        <Row>
          <Icon name='timer' width={18} height={18} fill='#6837FC' />
          <div className='ml-2'>
            Wait for{' '}
            {moment.duration(stageTrigger?.trigger_body?.wait_for).humanize()}{' '}
            to proceed to next action
          </div>
        </Row>
      )}

      {stageActions?.map((action) => (
        <Row key={action.id} className='mt-2'>
          {!isActionPending && (
            <Icon
              name='checkmark-circle'
              width={18}
              height={18}
              fill='#53af41'
            />
          )}
          {isActionPending && (
            <Icon name='radio' width={18} height={18} fill='#767d85' />
          )}
          <div className='ml-2'>
            {renderActionDetail(
              action.action_type,
              action.action_body.enabled,
              '',
            )}
          </div>
        </Row>
      ))}
    </div>
  )
}

const StageStatus = ({
  featureCurrentStageOrder,
  isCompleted,
  stageActions,
  stageEnvironment,
  stageName,
  stageOrder,
  stageTrigger,
  totalStages,
}: StageStatusProps) => {
  const isFeatureInStage = featureCurrentStageOrder === stageOrder
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
            'completed': isFeatureInStage,
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

interface FeaturePipelineStatusProps {
  featureId: number
  projectId: string
}

const FeaturePipelineStatus = ({
  featureId,
  projectId,
}: FeaturePipelineStatusProps) => {
  const { data: releasePipelines } = useGetReleasePipelinesQuery(
    {
      page_size: 100,
      projectId: Number(projectId),
      q: 'name',
    },
    {
      skip: !projectId,
    },
  )
  const matchingReleasePipeline = useMemo(
    () =>
      releasePipelines?.results?.find((pipeline) =>
        pipeline.features?.includes(featureId),
      ),
    [releasePipelines, featureId],
  )

  const { data: releasePipeline } = useGetReleasePipelineQuery(
    {
      pipelineId: matchingReleasePipeline?.id ?? NaN,
      projectId: Number(projectId),
    },
    {
      skip: !matchingReleasePipeline?.id,
    },
  )

  const stages = releasePipeline?.stages
  const totalStages = (stages?.length ?? 0) + 1

  const featureCurrentStageOrder = useMemo(
    () =>
      stages?.find((stage) => {
        const stageFeatureIds = Object.keys(stage.features ?? {})
        return stageFeatureIds.includes(featureId.toString())
      })?.order,
    [stages, featureId],
  )

  if (!stages) return null

  return (
    <AccordionCard title='Release Pipeline'>
      <Row className='flex mt-4 align-items-start justify-content-between'>
        {stages?.map((stage) => (
          <StageStatus
            key={stage.id}
            stageOrder={stage.order}
            stageName={stage.name}
            stageEnvironment={stage.environment}
            stageActions={stage.actions}
            stageTrigger={stage.trigger}
            totalStages={totalStages}
            featureCurrentStageOrder={featureCurrentStageOrder}
            isCompleted={
              featureCurrentStageOrder
                ? stage.order < featureCurrentStageOrder
                : false
            }
          />
        ))}
        <StageStatus
          stageOrder={totalStages - 1}
          stageName='Done'
          totalStages={totalStages}
          featureCurrentStageOrder={featureCurrentStageOrder}
        />
      </Row>
    </AccordionCard>
  )
}

export type { FeaturePipelineStatusProps }
export default FeaturePipelineStatus
