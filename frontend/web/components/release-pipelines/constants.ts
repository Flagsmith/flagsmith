import { StageTriggerType } from 'common/types/responses'

const TRIGGER_OPTIONS: { label: string; value: StageTriggerType }[] = [
  {
    label: 'When flag is added to this stage',
    value: StageTriggerType.ON_ENTER,
  },
  { label: 'Wait a set amount of time', value: StageTriggerType.WAIT_FOR },
]

const FLAG_ACTION_OPTIONS = [
  { label: 'Enable flag for everyone', value: 'TOGGLE_FEATURE' },
  { label: 'Disable flag for everyone', value: 'TOGGLE_FEATURE_DISABLE' },
  { label: 'Enable flag for segment', value: 'TOGGLE_FEATURE_FOR_SEGMENT' },
  {
    label: 'Disable flag for segment',
    value: 'TOGGLE_FEATURE_DISABLE_FOR_SEGMENT',
  },
]

// TODO: Validate value to be sent in the request
const TIME_UNIT_OPTIONS = [
  { label: 'Day(s)', value: 'day' },
  { label: 'Hour(s)', value: 'hour' },
  { label: 'Minute(s)', value: 'minute' },
]

export { TRIGGER_OPTIONS, FLAG_ACTION_OPTIONS, TIME_UNIT_OPTIONS }
