import { useGetSegmentsQuery } from 'common/services/useSegment'
import { StageActionRequest } from 'common/types/requests'

import { useMemo } from 'react'
import SinglePipelineStageAction from './SinglePipelineStageAction'

interface PipelineStageActionsProps {
  actions: StageActionRequest[]
  projectId: number
  onActionChange: (option: { value: string; label: string }) => void
  onSegmentChange: (option: { value: number; label: string }) => void
}

const PipelineStageActions = ({
  actions,
  onActionChange,
  onSegmentChange,
  projectId,
}: PipelineStageActionsProps) => {
  const { data: segments, isLoading: isSegmentsLoading } = useGetSegmentsQuery(
    {
      include_feature_specific: true,
      page_size: 1000,
      projectId,
    },
    { skip: !projectId },
  )

  const segmentOptions = useMemo(() => {
    return segments?.results?.map((segment) => ({
      label: segment.name,
      value: segment.id,
    }))
  }, [segments])

  if (!actions?.length) {
    return (
      <SinglePipelineStageAction
        onActionChange={onActionChange}
        onSegmentChange={onSegmentChange}
        isSegmentsLoading={isSegmentsLoading}
        segmentOptions={segmentOptions}
      />
    )
  }

  return (
    <>
      {actions.map((action, index) => (
        <SinglePipelineStageAction
          key={index}
          action={action}
          onActionChange={onActionChange}
          onSegmentChange={onSegmentChange}
          isSegmentsLoading={isSegmentsLoading}
          segmentOptions={segmentOptions}
        />
      ))}
    </>
  )
}

export default PipelineStageActions
