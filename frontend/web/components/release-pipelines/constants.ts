import { StageTriggerType } from 'common/types/responses'

const TRIGGER_OPTIONS = [
  { label: 'When flag is added to this stage', value: 'ON_ENTER' },
]

const FLAG_ACTIONS = {
  [StageTriggerType.ON_ENTER]: [
    { label: 'Enable flag for everyone', value: 'TOGGLE_FEATURE' },
    { label: 'Disable flag for everyone', value: 'TOGGLE_FEATURE_DISABLE' },
    { label: 'Enable flag for segment', value: 'TOGGLE_FEATURE_FOR_SEGMENT' },
    {
      label: 'Disable flag for segment',
      value: 'TOGGLE_FEATURE_DISABLE_FOR_SEGMENT',
    },
  ],
}

export { TRIGGER_OPTIONS, FLAG_ACTIONS }
