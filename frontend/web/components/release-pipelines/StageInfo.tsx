import { Environment } from 'common/types/responses'

import { PipelineStage } from 'common/types/responses'
import StageCard from './StageCard'
import StageArrow from './StageArrow'

type StageInfoProps = {
  environmentsData: Environment[] | undefined
  stageData: PipelineStage
}

const StageInfo = ({ environmentsData, stageData }: StageInfoProps) => {
  const environmentData = environmentsData?.find(
    (environment) => environment.id === stageData?.environment,
  )
  // TODO: After trigger_type and trigger_action is added, we can show the trigger text

  return (
    <Row>
      <Row className='align-items-start no-wrap'>
        <StageCard>
          <div>
            <h5>{stageData?.name}</h5>
            <p>{environmentData?.name}</p>
            <p className='text-muted'>
              <span>
                When flag is added to this stage, enable flag for{' '}
                <b>everyone</b>
              </span>
            </p>
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
