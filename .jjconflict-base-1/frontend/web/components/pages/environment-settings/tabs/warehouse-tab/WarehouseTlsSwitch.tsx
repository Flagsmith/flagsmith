import { FC } from 'react'
import Switch from 'components/Switch'
import FieldLabel from 'components/base/forms/FieldLabel'

type WarehouseTlsSwitchProps = {
  checked: boolean
  disabled?: boolean
  onChange?: (checked: boolean) => void
}

const WarehouseTlsSwitch: FC<WarehouseTlsSwitchProps> = ({
  checked,
  disabled,
  onChange,
}) => (
  <div className='wh-config-form__field'>
    <div className='d-flex flex-row align-items-center gap-2'>
      <Switch
        id='warehouse-config-secure'
        checked={checked}
        disabled={disabled}
        onChange={onChange}
      />
      <FieldLabel
        htmlFor='warehouse-config-secure'
        className='wh-config-form__label fs-caption text-secondary mb-0'
      >
        Secure connection (TLS)
      </FieldLabel>
    </div>
  </div>
)

WarehouseTlsSwitch.displayName = 'WarehouseTlsSwitch'
export default WarehouseTlsSwitch
