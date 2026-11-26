import { FC } from 'react'
import { NavLink, NavLinkProps } from 'react-router-dom'
import { useCloseDropdownMenu } from './DropdownMenuContext'

// A menu row that navigates; the current page gets the selected look.
// Children are the label, with an optional icon first.
const DropdownMenuLink: FC<NavLinkProps> = ({ children, onClick, ...rest }) => {
  const close = useCloseDropdownMenu()
  return (
    <NavLink
      {...rest}
      className='ds-dropdown-menu__item'
      onClick={(e) => {
        onClick?.(e)
        close()
      }}
    >
      <span className='ds-dropdown-menu__content'>
        <span className='ds-dropdown-menu__label'>{children}</span>
      </span>
    </NavLink>
  )
}

export default DropdownMenuLink
