import React, { FC, HTMLAttributes, ReactNode } from 'react'
import cn from 'classnames'

export type RowProps = HTMLAttributes<HTMLDivElement> & {
  children?: ReactNode
  className?: string
  space?: boolean
  noWrap?: boolean
}

const Row: FC<RowProps> = ({ children, className, noWrap, space, ...rest }) => {
  return (
    <div
      {...rest}
      className={cn(
        {
          'flex-row': true,
          noWrap,
          space,
        },
        className,
      )}
    >
      {children}
    </div>
  )
}

Row.displayName = 'Row'

export default Row
