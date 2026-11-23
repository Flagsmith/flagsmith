import React, { FC } from 'react'
import RCSwitch, { Props as RCSwitchProps } from 'rc-switch'

export type SwitchProps = RCSwitchProps & {
  id?: string
  checked?: boolean
  offMarkup?: React.ReactNode
  onMarkup?: React.ReactNode
  onChange?: (checked: boolean) => void
}

const Switch: FC<SwitchProps> = ({
  checked,
  offMarkup,
  onChange,
  onMarkup,
  ...rest
}) => {
  if (E2E) {
    return (
      <div className='d-inline-block' style={{ height: '28px' }}>
        <button
          role='switch'
          type='button'
          style={{
            color: 'black',
            pointerEvents: 'all',
          }}
          className={`position-relative ${
            checked ? 'switch-checked' : 'switch-unchecked'
          }`}
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

  return <RCSwitch checked={checked} onChange={onChange} {...rest} />
}

Switch.displayName = 'Switch'

export default Switch
