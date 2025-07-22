import { PipelineStageRequest, StageActionRequest } from 'common/types/requests'
import { StageActionType, StageTriggerType } from 'common/types/responses'

const TRIGGER_OPTIONS: { label: string; value: StageTriggerType }[] = [
  {
    label: 'When flag is added to this stage',
    value: StageTriggerType.ON_ENTER,
  },
  { label: 'Wait a set amount of time', value: StageTriggerType.WAIT_FOR },
]

const FLAG_ACTION_OPTIONS = [
  { label: 'Enable flag for everyone', value: StageActionType.TOGGLE_FEATURE },
  {
    label: 'Disable flag for everyone',
    value: `${StageActionType.TOGGLE_FEATURE}_DISABLE`,
  },
  {
    label: 'Enable flag for segment',
    value: StageActionType.TOGGLE_FEATURE_FOR_SEGMENT,
  },
  {
    label: 'Disable flag for segment',
    value: `${StageActionType.TOGGLE_FEATURE_FOR_SEGMENT}_DISABLE`,
  },
]

enum TimeUnit {
  DAY = 'days',
  HOUR = 'hours',
  MINUTE = 'minutes',
}

const TIME_UNIT_OPTIONS = [
  { label: 'Day(s)', value: TimeUnit.DAY },
  { label: 'Hour(s)', value: TimeUnit.HOUR },
  { label: 'Minute(s)', value: TimeUnit.MINUTE },
]

const NEW_PIPELINE_STAGE_ACTION_TYPE = ''
const NEW_PIPELINE_STAGE_ACTION = {
  action_body: { enabled: false },
  action_type: NEW_PIPELINE_STAGE_ACTION_TYPE,
} as StageActionRequest

const NEW_PIPELINE_STAGE: PipelineStageRequest = {
  actions: [NEW_PIPELINE_STAGE_ACTION],
  environment: -1,
  name: '',
  order: 0,
  trigger: {
    trigger_body: null,
    trigger_type: StageTriggerType.ON_ENTER,
  },
}

export {
  TRIGGER_OPTIONS,
  FLAG_ACTION_OPTIONS,
  TIME_UNIT_OPTIONS,
  TimeUnit,
  NEW_PIPELINE_STAGE,
  NEW_PIPELINE_STAGE_ACTION,
  NEW_PIPELINE_STAGE_ACTION_TYPE,
}
