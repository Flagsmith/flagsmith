import React, { FC, ReactNode } from 'react'
import Icon, { IconName } from './Icon'
import { NavLink, NavLinkProps } from 'react-router-dom'
import { Nav } from 'reactstrap'
import classNames from 'classnames'

type SidebarLinkType = Partial<NavLinkProps> & {
  icon?: ReactNode
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
    'fw-semibold text-primary bg-primary-opacity-5 fill-primary'
  const inactiveClassName = 'text-body fill-body'
  return (
    <Tag
      to={to}
      activeClassName={activeClassName}
      inactiveClassName={activeClassName}
      className={classNames(
        rest.className,
        'd-flex cursor-pointer align-items-center p-2 rounded',
        {
          [activeClassName]: active,
          [inactiveClassName]: !to && !active,
        },
      )}
      {...rest}
    >
      {!!icon && (
        <span className='mr-2 d-flex h-100 justify-content-center align-items-center'>
          {icon}
        </span>
      )}
      {children}
    </Tag>
  )
}

export default SidebarLink
