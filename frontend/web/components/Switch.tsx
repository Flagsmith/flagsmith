import React, { FC } from 'react'
import RCSwitch, { SwitchProps as RCSwitchProps } from 'rc-switch'
import Icon from './Icon'

export type SwitchProps = RCSwitchProps & {
  checked?: boolean
  darkMode?: boolean
  offMarkup?: React.ReactNode
  onMarkup?: React.ReactNode
  onChange?: (checked: boolean) => void
}

const Switch: FC<SwitchProps> = ({
  checked,
  darkMode,
  offMarkup,
  onChange,
  onMarkup,
  ...rest
}) => {
  if (E2E) {
    return (
      <div style={{ display: 'inline-block', height: '28px' }}>
        <button
          role='switch'
          type='button'
          style={{
            color: 'black',
            pointerEvents: 'all',
            position: 'relative',
          }}
          className={checked ? 'switch-checked' : 'switch-unchecked'}
          {...rest}
          onClick={() => {
            onChange?.(!checked)
          }}
        >
          {checked ? offMarkup || 'On' : onMarkup || 'Off'}
        </button>
      </div>
    )
  }

  if (darkMode) {
    return (
      <button
        role='switch'
        type='button'
        className={`rc-switch flex-row justify-content-center gap-3 ${
          checked ? 'rc-switch-checked' : 'rc-switch-unchecked'
        }`}
        {...rest}
        onClick={() => {
          onChange?.(!checked)
        }}
      >
        <Icon name='sun' fill={checked ? '#656D7B' : '#1A2634'} />
        <Icon name='moon' fill={checked ? '#FFFFFF' : '#9DA4AE'} />
      </button>
    )
  }

  return <RCSwitch checked={checked} onChange={onChange} {...rest} />
}

Switch.displayName = 'Switch'

export default Switch
