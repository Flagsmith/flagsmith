import React, { FC, ReactNode } from 'react'
import cn from 'classnames'

type DocsLinkProps = {
  href: string
  children: ReactNode
  className?: string
}

const DocsLink: FC<DocsLinkProps> = ({ children, className, href }) => (
  <a
    className={cn('btn-link fw-normal', className)}
    href={href}
    rel='noreferrer'
    target='_blank'
  >
    {children}
  </a>
)

export default DocsLink
