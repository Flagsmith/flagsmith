import React, { AnchorHTMLAttributes, ReactNode, Ref } from 'react'
import cn from 'classnames'
import {
  Link as RouterLink,
  LinkProps as RouterLinkProps,
} from 'react-router-dom'
import './Link.scss'

type LinkBaseProps = AnchorHTMLAttributes<HTMLAnchorElement> & {
  children: ReactNode
  ref?: Ref<HTMLAnchorElement>
}

// `to` stays in the app and does not reload it, `href` leaves. `to` takes the
// router's own type, so the object form carrying search or state works here too.
export type LinkProps = LinkBaseProps &
  ({ to: RouterLinkProps['to']; href?: never } | { href: string; to?: never })

// Use this to go somewhere and Button to do something.
const Link: React.FC<LinkProps> = ({
  children,
  className,
  href,
  ref,
  rel,
  target,
  to,
  ...rest
}) => {
  const classes = cn('link', className)

  if (to) {
    return (
      <RouterLink {...rest} className={classes} to={to} ref={ref}>
        {children}
      </RouterLink>
    )
  }

  return (
    <a
      {...rest}
      className={classes}
      href={href}
      target={target}
      // Stops the new tab getting a handle on this one.
      rel={target === '_blank' ? rel ?? 'noreferrer' : rel}
      ref={ref}
    >
      {children}
    </a>
  )
}

Link.displayName = 'Link'
export default Link
