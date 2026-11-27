import { FC, useId } from 'react'
import { NavLink, NavLinkProps } from 'react-router-dom'
import { useCloseDropdownMenu } from './DropdownMenuContext'
import DropdownMenuRow from './DropdownMenuRow'

// The row owns its styling, so it takes no className
const DropdownMenuLink: FC<Omit<NavLinkProps, 'className'>> = ({
  children,
  onClick,
  onKeyDown,
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
      // Menu rows answer Space like Enter; a link only answers Enter
      onKeyDown={(e) => {
        onKeyDown?.(e)
        if (e.key === ' ') {
          e.preventDefault()
          e.currentTarget.click()
        }
      }}
    >
      <DropdownMenuRow id={id}>{children}</DropdownMenuRow>
    </NavLink>
  )
}

export default DropdownMenuLink
