import { FC, ReactNode, useId } from 'react'
import classNames from 'classnames'
import BareButton from 'components/base/forms/BareButton'
import { useCloseDropdownMenu } from './DropdownMenuContext'
import DropdownMenuRow from './DropdownMenuRow'

export type DropdownMenuItemProps = {
  // The label, with an optional icon first: <Icon name='copy' /> Copy
  children: ReactNode
  onSelect: () => void
  // Makes the item one option of a single choice, ticked when true
  selected?: boolean
  destructive?: boolean
  disabled?: boolean
  description?: string
}

const DropdownMenuItem: FC<DropdownMenuItemProps> = ({
  children,
  description,
  destructive = false,
  disabled = false,
  onSelect,
  selected,
}) => {
  const close = useCloseDropdownMenu()
  const id = useId()
  const isOption = selected !== undefined
  // aria-disabled keeps it focusable, so the description stays reachable.
  // Named by the label alone, so the description is read once
  return (
    <BareButton
      className={classNames('ds-dropdown-menu__item', {
        'ds-dropdown-menu__item--destructive': destructive,
      })}
      role={isOption ? 'menuitemradio' : 'menuitem'}
      aria-checked={isOption ? selected : undefined}
      aria-disabled={disabled || undefined}
      aria-labelledby={description ? `${id}-label` : undefined}
      aria-describedby={description ? `${id}-description` : undefined}
      onClick={() => {
        if (disabled) return
        onSelect()
        close()
      }}
    >
      <DropdownMenuRow id={id} description={description} selected={selected}>
        {children}
      </DropdownMenuRow>
    </BareButton>
  )
}

export default DropdownMenuItem
