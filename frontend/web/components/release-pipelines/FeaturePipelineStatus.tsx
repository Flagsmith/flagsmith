import { useGetReleasePipelineQuery } from 'common/services/useReleasePipelines'
import AccordionCard from 'components/base/accordion/AccordionCard'
import ProjectStore from 'common/stores/project-store'

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

  const defaultStyle = {
    backgroundColor: 'white',
    border: '4px solid',
    borderColor: isInStage ? '#6837fc' : '#AAA',
    borderRadius: '50%',
    height: '24px',
    width: '24px',
    zIndex: 10,
  }

  const lineLeftStyle = {
    backgroundColor: '#AAA',
    height: '3px',
    left: '0%',
    top: '11px',
    width: '50%',
    zIndex: 1,
  }

  const lineRightStyle = {
    backgroundColor: '#AAA',
    height: '3px',
    left: '50%',
    top: '11px',
    width: 'calc(50% + 24px)',
    zIndex: 1,
  }
  const stageStyle = {
    marginRight: lastStage ? '0px' : '24px',
  }

  const env = ProjectStore.getEnvironmentById(stageEnvironment)

  return (
    <div
      className='flex align-items-center gap-2 position-relative flex-1'
      style={stageStyle}
    >
      {showLeftLine && (
        <div className='position-absolute' style={lineLeftStyle} />
      )}
      {showRightLine && (
        <div className='position-absolute' style={lineRightStyle} />
      )}
      <div style={defaultStyle} />
      <span>
        <b>{stageName}</b>
      </span>
      {env?.name && <p className='text-muted'>{env?.name}</p>}
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
