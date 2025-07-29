import React, { useMemo } from 'react'
import { useGetReleasePipelinesQuery } from 'common/services/useReleasePipelines'
import { ReleasePipeline } from 'common/types/responses'

interface FeatureInPipelineGuardProps {
  projectId: number
  featureId: number
  children: React.ReactNode
  renderFallback: (matchingReleasePipeline: ReleasePipeline) => React.ReactNode
  skip?: boolean
}

const FeatureInPipelineGuard: React.FC<FeatureInPipelineGuardProps> = ({
  children,
  featureId,
  projectId,
  renderFallback,
  skip = false,
}) => {
  const { data: releasePipelines } = useGetReleasePipelinesQuery(
    {
      projectId,
    },
    {
      skip: skip || !projectId || !featureId,
    },
  )

  const matchingReleasePipeline = useMemo(() => {
    if (!featureId || !releasePipelines?.results) {
      return undefined
    }

    return releasePipelines.results.find((pipeline) =>
      pipeline.features?.includes(featureId),
    )
  }, [releasePipelines, featureId])

  const isFeatureInReleasePipeline = !!matchingReleasePipeline?.id

  if (!isFeatureInReleasePipeline) {
    return <>{children}</>
  }

  return <>{renderFallback(matchingReleasePipeline)}</>
}

export default FeatureInPipelineGuard
