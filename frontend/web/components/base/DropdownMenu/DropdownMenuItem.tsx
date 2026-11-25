import { FC, MouseEvent, ReactNode, useId } from 'react'
import classNames from 'classnames'
import BareButton from 'components/base/forms/BareButton'
import Icon, { IconName } from 'components/icons/Icon'
import { useCloseDropdownMenu } from './DropdownMenuContext'

export type DropdownMenuItemProps = {
  children: ReactNode
  onSelect: (e: MouseEvent<HTMLButtonElement>) => void
  icon?: IconName
  // The selected option, as in a section switcher: ticked and announced
  current?: boolean
  destructive?: boolean
  disabled?: boolean
  // Shown on hover while disabled
  disabledReason?: string
}

const DropdownMenuItem: FC<DropdownMenuItemProps> = ({
  children,
  current = false,
  destructive = false,
  disabled = false,
  disabledReason,
  icon,
  onSelect,
}) => {
  const close = useCloseDropdownMenu()
  const id = useId()
  const reasonId = `${id}-reason`
  const reason = disabled ? disabledReason : undefined
  // aria-disabled keeps the item focusable, and the reason shows under the
  // label, so keyboard and touch users both get it. Named by the label alone,
  // so the reason is read once, as the description
  return (
    <BareButton
      className={classNames('ds-dropdown-menu__item', {
        'ds-dropdown-menu__item--destructive': destructive,
      })}
      aria-current={current || undefined}
      aria-disabled={disabled || undefined}
      aria-labelledby={reason ? `${id}-label` : undefined}
      aria-describedby={reason ? reasonId : undefined}
      onClick={(e) => {
        if (disabled) return
        onSelect(e)
        close()
      }}
    >
      {icon && (
        <span className='ds-dropdown-menu__icon' aria-hidden>
          <Icon name={icon} width={16} />
        </span>
      )}
      <span className='ds-dropdown-menu__label'>
        <span id={`${id}-label`}>{children}</span>
        {reason && (
          <span id={reasonId} className='ds-dropdown-menu__reason'>
            {reason}
          </span>
        )}
      </span>
      {current && (
        <span className='ds-dropdown-menu__icon' aria-hidden>
          <Icon name='checkmark' width={16} />
        </span>
      )}
    </BareButton>
  )
}

export default DropdownMenuItem
