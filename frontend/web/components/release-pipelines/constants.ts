const TRIGGER_OPTIONS = [
  { label: 'When flag is added to this stage', value: 'ON_ENTER' },
]

const FLAG_ACTIONS = {
  'ON_ENTER': [
    { label: 'Enable flag for everyone', value: 'ENABLE_FEATURE' },
    { label: 'Disable flag for everyone', value: 'DISABLE_FEATURE' },
    { label: 'Enable flag for segment', value: 'ENABLE_FEATURE_FOR_SEGMENT' },
    { label: 'Disable flag for segment', value: 'DISABLE_FEATURE_FOR_SEGMENT' },
  ],
}

export { TRIGGER_OPTIONS, FLAG_ACTIONS }
