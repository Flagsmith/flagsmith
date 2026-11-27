import React, { FC, ReactNode } from 'react'
import { NavLink, NavLinkProps } from 'react-router-dom'
import classNames from 'classnames'
import { IconComponent } from 'components/icons'

type SidebarLinkType = Partial<NavLinkProps> & {
  icon?: IconComponent
  children?: ReactNode
  to?: string
  active?: boolean
  onClick?: () => void
}

const SidebarLink: FC<SidebarLinkType> = ({
  active,
  children,
  icon: Icon,
  to,
  ...rest
}) => {
  const Tag = (to ? NavLink : 'div') as any

  return (
    <Tag
      {...rest}
      to={to}
      activeClassName='sidebar-link--active'
      exact={true}
      className={classNames(
        rest.className,
        'sidebar-link d-flex gap-2 cursor-pointer align-items-center p-2 rounded',
        {
          'sidebar-link--active': !to && active,
        },
      )}
    >
      {!!Icon && <Icon width={18} />}
      {children}
    </Tag>
  )
}

export default SidebarLink
