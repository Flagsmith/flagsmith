import { StageTriggerBody, StageTriggerType } from 'common/types/responses'

import { PipelineStage } from 'common/types/responses'
import StageCard from './StageCard'
import StageArrow from './StageArrow'
import moment from 'moment'
import StageFeatureDetail from './StageFeatureDetail'
import FlagActionDetail from './FlagActionDetail'

type StageInfoProps = {
  environmentName: string
  stageData: PipelineStage
  projectId: number
}

const getTriggerText = (
  triggerType: StageTriggerType,
  triggerBody: StageTriggerBody,
) => {
  if (triggerType === StageTriggerType.ON_ENTER) {
    return <span>When flag is added to this stage</span>
  }

  if (triggerType === StageTriggerType.WAIT_FOR) {
    return (
      <span>Wait for {moment.duration(triggerBody?.wait_for).humanize()}</span>
    )
  }

  return null
}

const StageInfo = ({
  environmentName,
  projectId,
  stageData,
}: StageInfoProps) => {
  return (
    <Row>
      <Row className='align-items-start no-wrap'>
        <StageCard>
          <div>
            <h5>{stageData?.name}</h5>
            <p>{environmentName}</p>
            <p className='text-muted'>
              {getTriggerText(
                stageData?.trigger?.trigger_type,
                stageData?.trigger?.trigger_body,
              )}
              {stageData?.actions?.map((action) => {
                return (
                  <div key={action.id}>
                    <FlagActionDetail
                      actionBody={action.action_body}
                      actionType={action.action_type}
                      projectId={projectId}
                    />
                  </div>
                )
              })}
            </p>
            <StageFeatureDetail
              features={stageData?.features}
              projectId={projectId}
            />
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
