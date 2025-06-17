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

const TIME_UNIT_OPTIONS = [
  { label: 'Day(s)', value: 'days' },
  { label: 'Hour(s)', value: 'hour' },
  { label: 'Minute(s)', value: 'minute' },
]

export { TRIGGER_OPTIONS, FLAG_ACTION_OPTIONS, TIME_UNIT_OPTIONS }
