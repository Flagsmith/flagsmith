import { FC, MouseEvent, ReactNode, useId } from 'react'
import classNames from 'classnames'
import BareButton from 'components/base/forms/BareButton'
import Icon from 'components/icons/Icon'
import { useCloseDropdownMenu } from './DropdownMenuContext'

export type DropdownMenuItemProps = {
  // The label, with an optional icon first: <Icon name='copy' /> Copy
  children: ReactNode
  onSelect: (e: MouseEvent<HTMLButtonElement>) => void
  // The selected option, as in a section switcher: ticked and announced
  current?: boolean
  destructive?: boolean
  disabled?: boolean
  // Shown under the label while disabled
  disabledReason?: string
}

const DropdownMenuItem: FC<DropdownMenuItemProps> = ({
  children,
  current = false,
  destructive = false,
  disabled = false,
  disabledReason,
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
      <span className='ds-dropdown-menu__content'>
        <span id={`${id}-label`} className='ds-dropdown-menu__label'>
          {children}
        </span>
        {reason && (
          <span id={reasonId} className='ds-dropdown-menu__reason'>
            {reason}
          </span>
        )}
      </span>
      {current && (
        <Icon
          name='checkmark'
          className='ds-dropdown-menu__check'
          aria-hidden
        />
      )}
    </BareButton>
  )
}

export default DropdownMenuItem
