import React, { FC, HTMLAttributes } from 'react'
import cn from 'classnames'

type SkeletonVariant = 'text' | 'badge' | 'circle'

type SkeletonProps = HTMLAttributes<HTMLDivElement> & {
  width?: number | string
  height?: number | string
  variant?: SkeletonVariant
}

const variantClassNames: Record<SkeletonVariant, string> = {
  badge: 'skeleton-badge',
  circle: 'skeleton-circle',
  text: 'skeleton-text',
}

const Skeleton: FC<SkeletonProps> = ({
  className,
  height,
  variant = 'text',
  width,
  ...rest
}) => (
  <div
    className={cn('skeleton', variantClassNames[variant], className)}
    style={{ height, width }}
    {...rest}
  />
)

Skeleton.displayName = 'Skeleton'

export default Skeleton
export type { SkeletonProps, SkeletonVariant }
