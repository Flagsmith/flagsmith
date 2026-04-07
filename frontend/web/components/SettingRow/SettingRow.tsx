import React, { FC, HTMLAttributes, ReactNode, useId } from 'react'
import cn from 'classnames'
import Switch from 'components/Switch'
import './setting-row.scss'

type SettingRowProps = HTMLAttributes<HTMLDivElement> & {
  title: ReactNode
  description: ReactNode
  checked: boolean
  disabled?: boolean
  onChange?: (checked: boolean) => void
}

const SettingRow: FC<SettingRowProps> = ({
  checked,
  className,
  description,
  disabled = false,
  onChange,
  title,
  ...rest
}) => {
  const id = useId()
  const titleId = `${id}-title`
  const descId = `${id}-desc`

  return (
    <div className={cn('setting-row', className)} {...rest}>
      <div className='setting-row__header'>
        <div className='setting-row__switch'>
          <Switch
            checked={checked}
            disabled={disabled}
            onChange={onChange}
            aria-labelledby={titleId}
            aria-describedby={descId}
          />
        </div>
        <h5 id={titleId} className='setting-row__title'>
          {title}
        </h5>
      </div>
      <small id={descId} className='setting-row__description'>
        {description}
      </small>
    </div>
  )
}

SettingRow.displayName = 'SettingRow'

export default SettingRow
export type { SettingRowProps }
