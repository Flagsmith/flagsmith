import React, { FC } from 'react'
import { NavLink, NavLinkProps } from 'react-router-dom'
import Icon, { IconName } from './Icon'

type EnvironmentLinkType = NavLinkProps & {
  icon: IconName
}
const activeClassName = 'text-primary fill-primary bg-primary-opacity-5'

const EnvironmentLink: FC<EnvironmentLinkType> = ({
  children,
  icon,
  ...rest
}) => {
  return (
    <NavLink
      {...rest}
      className='d-flex gap-2 py-1 px-2 hover-fill-primary rounded align-items-center text-nowrap'
      activeClassName={activeClassName}
    >
      <Icon width={18} name={icon} fill={'#767D85'} />
      {children}
    </NavLink>
  )
}

export default EnvironmentLink
