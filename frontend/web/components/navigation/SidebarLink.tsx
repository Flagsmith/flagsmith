import React, { FC, ReactNode } from 'react'
import { NavLink, NavLinkProps } from 'react-router-dom'
import classNames from 'classnames'
import Icon, { IconName } from 'components/Icon'

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
  const activeClassName =
    'text-primary fw-semibold bg-primary-opacity-5 fill-primary'
  const inactiveClassName = 'text-body fill-body'
  return (
    <Tag
      {...rest}
      to={to}
      activeClassName={activeClassName}
      inactiveClassName={activeClassName}
      className={classNames(
        rest.className,
        'd-flex hover-fill-primary hover-bg-primary gap-2 cursor-pointer align-items-center p-2 rounded',
        {
          [activeClassName]: active,
          [inactiveClassName]: !to && !active,
        },
      )}
    >
      {!!icon && <Icon width={18} name={icon} fill={'#767D85'} />}
      {children}
    </Tag>
  )
}

export default SidebarLink
