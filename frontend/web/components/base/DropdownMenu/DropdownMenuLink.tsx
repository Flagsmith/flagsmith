import { FC, useId } from 'react'
import { NavLink, NavLinkProps } from 'react-router-dom'
import { useCloseDropdownMenu } from './DropdownMenuContext'
import DropdownMenuRow from './DropdownMenuRow'

// A menu row that navigates; the current page gets the selected look.
// Children are the label, with an optional icon first.
// The row owns its styling, so it takes no className
const DropdownMenuLink: FC<Omit<NavLinkProps, 'className'>> = ({
  children,
  onClick,
  ...rest
}) => {
  const close = useCloseDropdownMenu()
  const id = useId()
  return (
    <NavLink
      {...rest}
      role='menuitem'
      className='ds-dropdown-menu__item'
      onClick={(e) => {
        onClick?.(e)
        close()
      }}
    >
      <DropdownMenuRow id={id}>{children}</DropdownMenuRow>
    </NavLink>
  )
}

export default DropdownMenuLink
