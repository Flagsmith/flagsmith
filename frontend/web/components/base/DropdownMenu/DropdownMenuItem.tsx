import { FC, MouseEvent, ReactNode } from 'react'
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
}

const DropdownMenuItem: FC<DropdownMenuItemProps> = ({
  children,
  current = false,
  destructive = false,
  disabled = false,
  icon,
  onSelect,
}) => {
  const close = useCloseDropdownMenu()
  return (
    <BareButton
      className={classNames('ds-dropdown-menu__item', {
        'ds-dropdown-menu__item--destructive': destructive,
      })}
      aria-current={current || undefined}
      disabled={disabled}
      onClick={(e) => {
        onSelect(e)
        close()
      }}
    >
      {icon && (
        <span className='ds-dropdown-menu__icon' aria-hidden>
          <Icon name={icon} width={18} />
        </span>
      )}
      <span className='ds-dropdown-menu__label'>{children}</span>
      {current && (
        <span className='ds-dropdown-menu__icon' aria-hidden>
          <Icon name='checkmark' width={18} />
        </span>
      )}
    </BareButton>
  )
}

export default DropdownMenuItem
