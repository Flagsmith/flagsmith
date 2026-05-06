import React, {
  AnchorHTMLAttributes,
  FC,
  HTMLAttributeAnchorTarget,
  ReactNode,
} from 'react'
import cn from 'classnames'

type LinkProps = {
  href: string
  children: ReactNode
  /**
   * When true, opens in a new tab and adds `rel="noreferrer"`. Defaults to
   * `true` when `href` starts with `http(s)://`, `false` otherwise.
   */
  external?: boolean
  /** Drops the hover underline. Defaults to `false` (underline shown). */
  noUnderline?: boolean
  className?: string
  target?: HTMLAttributeAnchorTarget
  rel?: string
  onClick?: AnchorHTMLAttributes<HTMLAnchorElement>['onClick']
}

const Link: FC<LinkProps> = ({
  children,
  className,
  external,
  href,
  noUnderline = false,
  onClick,
  rel,
  target,
}) => {
  const isExternal = external ?? /^https?:\/\//.test(href)
  return (
    <a
      className={cn('btn-link', { 'no-underline': noUnderline }, className)}
      href={href}
      onClick={onClick}
      rel={rel ?? (isExternal ? 'noreferrer' : undefined)}
      target={target ?? (isExternal ? '_blank' : undefined)}
    >
      {children}
    </a>
  )
}

export default Link
