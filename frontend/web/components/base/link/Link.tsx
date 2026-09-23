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
type LinkDestination =
  | { to: RouterLinkProps['to']; href?: never }
  | { href: string; to?: never }

export type LinkProps = LinkBaseProps & LinkDestination

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
  // Stops a new tab getting a handle on this one.
  const safeRel = target === '_blank' ? rel ?? 'noreferrer' : rel

  // Not truthiness: `to=''` would render an anchor with no href.
  if (to !== undefined) {
    return (
      <RouterLink
        {...rest}
        className={classes}
        to={to}
        target={target}
        rel={safeRel}
        ref={ref}
      >
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
      rel={safeRel}
      ref={ref}
    >
      {children}
    </a>
  )
}

Link.displayName = 'Link'
export default Link
