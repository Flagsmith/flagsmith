import { useGetReleasePipelineQuery } from 'common/services/useReleasePipelines'
import AccordionCard from 'components/base/accordion/AccordionCard'
import ProjectStore from 'common/stores/project-store'
import { Environment } from 'common/types/responses'
import classNames from 'classnames'

interface StageStatusProps {
  featureId: number
  stageOrder: number
  stageName: string
  totalStages: number
  stageFeatures: number[]
  stageEnvironment?: number
}

const StageStatus = ({
  featureId,
  stageEnvironment,
  stageFeatures,
  stageName,
  stageOrder,
  totalStages,
}: StageStatusProps) => {
  const isInStage = stageFeatures?.includes(featureId) ?? false
  const showLine = totalStages > 1
  const lastStage = stageOrder === totalStages - 1
  const showLeftLine = showLine && stageOrder > 0
  const showRightLine = showLine && stageOrder !== totalStages - 1

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
      {showLeftLine && <div className='position-absolute line-left' />}
      {showRightLine && <div className='position-absolute line-right' />}
      <div
        className={classNames('circle-container', { 'in-stage': isInStage })}
      />
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
  releasePipelineId: number
}

const FeaturePipelineStatus = ({
  featureId,
  projectId,
  releasePipelineId,
}: FeaturePipelineStatusProps) => {
  const { data: releasePipeline } = useGetReleasePipelineQuery(
    {
      pipelineId: releasePipelineId,
      projectId: Number(projectId),
    },
    {
      skip: !releasePipelineId,
    },
  )

  const stages = releasePipeline?.stages
  const totalStages = (stages?.length ?? 0) + 1

  if (!stages) return null

  return (
    <AccordionCard title='Release Pipeline' defaultOpen>
      <Row className='flex mt-4 align-items-start justify-content-between'>
        {stages?.map((stage) => (
          <StageStatus
            key={stage.id}
            stageOrder={stage.order}
            stageName={stage.name}
            stageFeatures={stage.features}
            stageEnvironment={stage.environment}
            totalStages={totalStages}
            featureId={featureId}
          />
        ))}
        <StageStatus
          stageOrder={totalStages - 1}
          stageName='Done'
          stageFeatures={[]}
          totalStages={totalStages}
          featureId={featureId}
        />
      </Row>
    </AccordionCard>
  )
}

export type { FeaturePipelineStatusProps }
export default FeaturePipelineStatus
