import {
  useGetReleasePipelineQuery,
  useGetReleasePipelinesQuery,
} from 'common/services/useReleasePipelines'
import AccordionCard from 'components/base/accordion/AccordionCard'
import { useMemo } from 'react'

import StageStatus from './StageStatus'

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

  const stageHasFeature = useMemo(
    () =>
      stages?.find((stage) => {
        const stageFeatureIds = Object.keys(stage.features ?? {})
        return stageFeatureIds.includes(featureId.toString())
      }),
    [stages, featureId],
  )

  const featureInStage = useMemo(
    () => stageHasFeature?.features?.[featureId],
    [stageHasFeature, featureId],
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
            featureInStage={
              stageHasFeature?.order === stage.order
                ? featureInStage
                : undefined
            }
            isCompleted={stage.order < (stageHasFeature?.order ?? NaN)}
          />
        ))}
        <StageStatus
          stageOrder={totalStages - 1}
          stageName='Done'
          totalStages={totalStages}
        />
      </Row>
    </AccordionCard>
  )
}

export type { FeaturePipelineStatusProps }
export default FeaturePipelineStatus
