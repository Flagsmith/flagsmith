import React, { FC } from 'react'
import RCSwitch, { Props as RCSwitchProps } from 'rc-switch'
import { colorSurfaceAction, colorSurfaceEmphasis } from 'common/theme/tokens'
import Icon from './icons/Icon'

type EditableSwitchProps = RCSwitchProps & {
  id?: string
  checked?: boolean
  offMarkup?: React.ReactNode
  onMarkup?: React.ReactNode
  onChange?: (checked: boolean) => void
  readOnly?: false
}

// Shows a state that can't be changed here, e.g. in a table row.
type ReadOnlySwitchProps = {
  checked: boolean
  readOnly: true
  // What the state is about, e.g. "Admin" is read as "Admin: On".
  label?: string
  onChange?: never
  disabled?: never
}

export type SwitchProps = EditableSwitchProps | ReadOnlySwitchProps

const ReadOnlySwitch: FC<Omit<ReadOnlySwitchProps, 'readOnly'>> = ({
  checked,
  label,
}) => {
  const state = checked ? 'On' : 'Off'
  return (
    <Icon
      name={checked ? 'toggle-on' : 'toggle-off'}
      width={32}
      fill={checked ? colorSurfaceAction : colorSurfaceEmphasis}
      role='img'
      aria-label={label ? `${label}: ${state}` : state}
    />
  )
}

const EditableSwitch: FC<EditableSwitchProps> = ({
  checked,
  offMarkup,
  onChange,
  onMarkup,
  readOnly: _,
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

const Switch: FC<SwitchProps> = (props) =>
  props.readOnly ? (
    <ReadOnlySwitch checked={props.checked} label={props.label} />
  ) : (
    <EditableSwitch {...props} />
  )

Switch.displayName = 'Switch'

export default Switch
