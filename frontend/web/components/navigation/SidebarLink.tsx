import React, { FC, ReactNode } from 'react'
import { NavLink, NavLinkProps } from 'react-router-dom'
import classNames from 'classnames'
import Icon, { IconName } from 'components/icons/Icon'

type SidebarLinkType = Partial<NavLinkProps> & {
  icon?: IconName
  children?: ReactNode
  to?: string
  active?: boolean
  onClick?: () => void
}

const SidebarLink: FC<SidebarLinkType> = ({
  active,
  children,
  icon,
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
      {!!icon && <Icon width={18} name={icon} />}
      {children}
    </Tag>
  )
}

export default SidebarLink
