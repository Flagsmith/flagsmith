import React, { FC, ReactNode } from 'react'
import { LinkProps, NavLink } from 'react-router-dom'
import { IonIcon } from '@ionic/react'
import classNames from 'classnames'

type NavSubLinkType = LinkProps & {
  icon: string | ReactNode
  children: ReactNode
  disabled?: boolean
  tooltip?: string
  to?: string
}

const NavSubLink: FC<NavSubLinkType> = ({
  children,
  disabled,
  icon,
  to,
  tooltip,
  ...rest
}) => {
  return (
    <NavLink
      to={to}
      onClick={disabled ? (e) => e.preventDefault() : undefined}
      {...rest}
      activeClassName={!disabled ? 'active' : ''}
      className={classNames(rest.className, 'pt-2 nav-sub-link')}
    >
      <div
        className={classNames(
          'd-flex gap-2 nav-sub-link-inner align-items-center',
          disabled && 'nav-sub-link-disabled',
        )}
      >
        {typeof icon === 'string' ? <IonIcon icon={icon} /> : icon}
        {tooltip ? (
          <Tooltip place='top' title={children}>
            {tooltip}
          </Tooltip>
        ) : (
          children
        )}
      </div>
    </NavLink>
  )
}

export default NavSubLink
