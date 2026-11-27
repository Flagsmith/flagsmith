import { FC, ReactNode } from 'react'
import Icon from 'components/icons/Icon'

type DropdownMenuRowProps = {
  // Prefix for the label and description ids
  id: string
  children: ReactNode
  description?: string
  selected?: boolean
}

const DropdownMenuRow: FC<DropdownMenuRowProps> = ({
  children,
  description,
  id,
  selected,
}) => (
  <>
    <span className='ds-dropdown-menu__content'>
      <span id={`${id}-label`} className='ds-dropdown-menu__label'>
        {children}
      </span>
      {description && (
        <span
          id={`${id}-description`}
          className='ds-dropdown-menu__description'
        >
          {description}
        </span>
      )}
    </span>
    {selected && (
      <Icon name='checkmark' className='ds-dropdown-menu__check' aria-hidden />
    )}
  </>
)

export default DropdownMenuRow
