import React, { FC, ReactNode } from 'react'
import cn from 'classnames'
import Icon, { IconName } from 'components/icons/Icon'
import './banner.scss'

type BannerVariant = 'success' | 'warning' | 'danger' | 'info'

type BannerProps = {
  variant: BannerVariant
  children: ReactNode
}

const variantIcons: Record<BannerVariant, IconName> = {
  danger: 'close-circle',
  info: 'info',
  success: 'checkmark-circle',
  warning: 'warning',
}

const Banner: FC<BannerProps> = ({ children, variant }) => (
  <div className={cn('banner', `banner--${variant}`)}>
    <Icon name={variantIcons[variant]} fill={`var(--color-icon-${variant})`} />
    {children}
  </div>
)

Banner.displayName = 'Banner'

export default Banner
export type { BannerProps, BannerVariant }
