import { useGetSegmentsQuery } from 'common/services/useSegment'
import { StageActionRequest } from 'common/types/requests'

import { useMemo } from 'react'
import SinglePipelineStageAction from './SinglePipelineStageAction'
import Button from 'components/base/forms/Button'

interface PipelineStageActionsProps {
  actions: StageActionRequest[]
  projectId: number
  onAddAction: () => void
  onRemoveAction: (actionIndex: number) => void
  onActionChange: (
    option: { value: string; label: string },
    stageIndex: number,
  ) => void
  onSegmentChange: (
    option: { value: number; label: string },
    stageIndex: number,
  ) => void
}

const PipelineStageActions = ({
  actions,
  onActionChange,
  onAddAction,
  onRemoveAction,
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

  return (
    <>
      {actions?.map((action, index) => (
        <SinglePipelineStageAction
          key={index}
          actionIndex={index}
          action={action}
          onActionChange={onActionChange}
          onSegmentChange={onSegmentChange}
          isSegmentsLoading={isSegmentsLoading}
          segmentOptions={segmentOptions}
          onRemoveAction={index > 0 ? onRemoveAction : undefined}
        />
      ))}
      <Button iconLeft='plus' className='w-100' onClick={onAddAction}>
        Add Flag Action
      </Button>
    </>
  )
}

export default PipelineStageActions
