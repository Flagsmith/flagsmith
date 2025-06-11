import { StageTriggerType, Segment } from 'common/types/responses'

import { PipelineStage } from 'common/types/responses'
import StageCard from './StageCard'
import StageArrow from './StageArrow'

type StageInfoProps = {
  environmentName: string
  stageData: PipelineStage
  projectId: number
}

const getTriggerText = (
  triggerType: StageTriggerType,
  segmentData?: Segment,
) => {
  if (triggerType === StageTriggerType.ON_ENTER) {
    return (
      <span>
        When flag is added to this stage, enable flag for{' '}
        <b>{segmentData?.name ?? 'everyone'}</b>
      </span>
    )
  }

  return null
}

const StageInfo = ({ environmentName, stageData }: StageInfoProps) => {
  return (
    <Row>
      <Row className='align-items-start no-wrap'>
        <StageCard>
          <div>
            <h5>{stageData?.name}</h5>
            <p>{environmentName}</p>
            <p className='text-muted'>
              {/* TODO: Add segment data */}
              {getTriggerText(stageData?.trigger?.trigger_type, undefined)}
            </p>
            {/* TODO: Add features count */}
            <h6>Features (0)</h6>
            <p className='text-muted'>No features added to this stage yet.</p>
          </div>
        </StageCard>
        <div className='flex-1'>
          <StageArrow showAddStageButton={false} />
        </div>
      </Row>
    </Row>
  )
}

export type { StageInfoProps }
export default StageInfo
