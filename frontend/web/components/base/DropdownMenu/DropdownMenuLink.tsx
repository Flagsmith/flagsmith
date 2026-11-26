import { FC, ReactNode } from 'react'
import { NavLink, NavLinkProps } from 'react-router-dom'
import { useCloseDropdownMenu } from './DropdownMenuContext'

type DropdownMenuLinkProps = Pick<NavLinkProps, 'to' | 'exact' | 'isActive'> & {
  // The label, with an optional icon first
  children: ReactNode
}

// A menu row that navigates; the current page gets the selected look
const DropdownMenuLink: FC<DropdownMenuLinkProps> = ({ children, ...rest }) => {
  const close = useCloseDropdownMenu()
  return (
    <NavLink {...rest} className='ds-dropdown-menu__item' onClick={close}>
      <span className='ds-dropdown-menu__content'>
        <span className='ds-dropdown-menu__label'>{children}</span>
      </span>
    </NavLink>
  )
}

export default DropdownMenuLink
