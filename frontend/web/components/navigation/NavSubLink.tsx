import React, { FC, ReactNode } from 'react'
import type * as H from 'history';
import { LinkProps, NavLink, match } from 'react-router-dom'
import { IonIcon } from '@ionic/react'
import classNames from 'classnames'

type NavSubLinkType = LinkProps & {
  icon: string | ReactNode
  children: ReactNode
  isActive?<Params extends { [K in keyof Params]?: string }, S = unknown>(
    match: match<Params> | null,
    location: H.Location<S>
  ): boolean;
}

const NavSubLink: FC<NavSubLinkType> = ({ children, icon, isActive, ...rest }) => {
  return (
    <NavLink
      {...rest}
      isActive={isActive}
      activeClassName='active'
      className={classNames(rest.className, 'py-md-2 py-1 px-1 nav-sub-link')}
    >
      <div className='d-flex gap-2 text-nowrap nav-sub-link-inner align-items-center'>
        {typeof icon === 'string' ? <IonIcon icon={icon} /> : icon}
        {children}
      </div>
    </NavLink>
  )
}

export default NavSubLink
