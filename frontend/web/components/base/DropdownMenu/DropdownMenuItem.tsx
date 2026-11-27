import { FC, ReactNode, useId } from 'react'
import classNames from 'classnames'
import BareButton from 'components/base/forms/BareButton'
import Icon from 'components/icons/Icon'
import { useCloseDropdownMenu } from './DropdownMenuContext'

export type DropdownMenuItemProps = {
  // The label, with an optional icon first: <Icon name='copy' /> Copy
  children: ReactNode
  onSelect: () => void
  // The selected option, as in a section switcher: ticked and announced
  selected?: boolean
  destructive?: boolean
  disabled?: boolean
  // A second line under the label, such as why the item is disabled
  description?: string
}

const DropdownMenuItem: FC<DropdownMenuItemProps> = ({
  children,
  description,
  destructive = false,
  disabled = false,
  onSelect,
  selected = false,
}) => {
  const close = useCloseDropdownMenu()
  const id = useId()
  const descriptionId = `${id}-description`
  // aria-disabled keeps the item focusable, so a disabled item's description
  // still reaches keyboard and touch users. Named by the label alone, so the
  // description is read once
  return (
    <BareButton
      className={classNames('ds-dropdown-menu__item', {
        'ds-dropdown-menu__item--destructive': destructive,
      })}
      aria-current={selected || undefined}
      aria-disabled={disabled || undefined}
      aria-labelledby={description ? `${id}-label` : undefined}
      aria-describedby={description ? descriptionId : undefined}
      onClick={() => {
        if (disabled) return
        onSelect()
        close()
      }}
    >
      <span className='ds-dropdown-menu__content'>
        <span id={`${id}-label`} className='ds-dropdown-menu__label'>
          {children}
        </span>
        {description && (
          <span id={descriptionId} className='ds-dropdown-menu__description'>
            {description}
          </span>
        )}
      </span>
      {selected && (
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
