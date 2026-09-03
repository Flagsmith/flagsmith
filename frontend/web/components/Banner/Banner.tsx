import { FC, ReactNode } from 'react'
import cn from 'classnames'
import Icon, { IconName } from 'components/icons/Icon'
import './Banner.scss'

export type BannerVariant = 'success' | 'warning' | 'danger' | 'info'

export type BannerProps = {
  variant: BannerVariant
  children: ReactNode
  className?: string
}

const variantIcons: Record<BannerVariant, IconName> = {
  danger: 'close-circle',
  info: 'info',
  success: 'checkmark-circle',
  warning: 'warning',
}

// Only danger interrupts. The rest are read in place, so announcing them would
// talk over whatever the user was doing.
const isUrgent = (variant: BannerVariant) => variant === 'danger'

const Banner: FC<BannerProps> = ({ children, className, variant }) => (
  <div
    role={isUrgent(variant) ? 'alert' : undefined}
    className={cn('banner', `banner--${variant}`, className)}
  >
    <Icon
      aria-hidden
      name={variantIcons[variant]}
      fill={`var(--color-icon-${variant})`}
    />
    {children}
  </div>
)

export default Banner
