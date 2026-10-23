import { FC, ReactNode } from 'react'
import cn from 'classnames'
import Icon, { IconName } from 'components/icons/Icon'
import './Banner.scss'

export type BannerType = 'info' | 'success' | 'warning' | 'error'

// The spec draws a filled icon per type. We do not have filled variants yet, so
// these are the closest outlined ones in Icon.tsx.
const ICONS: Record<BannerType, IconName> = {
  error: 'warning',
  info: 'info',
  success: 'checkmark-circle',
  warning: 'warning',
}

// Most icons hardcode a fill on the path, so a fill in CSS never reaches them.
// Pass the colour in instead.
const ICON_COLOURS: Record<BannerType, string> = {
  error: 'var(--color-icon-danger)',
  info: 'var(--color-icon-info)',
  success: 'var(--color-icon-success)',
  warning: 'var(--color-icon-warning)',
}

export type BannerProps = {
  type?: BannerType
  // Shown in the type's colour. Omit for a single line of body text.
  title?: ReactNode
  children: ReactNode
  // Sits at the end of the row, for an action or a dismiss control.
  action?: ReactNode
  className?: string
}

const Banner: FC<BannerProps> = ({
  action,
  children,
  className,
  title,
  type = 'info',
}) => (
  <div
    // An error is announced as soon as it lands; the rest wait their turn.
    role={type === 'error' ? 'alert' : 'status'}
    className={cn('ds-banner', `ds-banner--${type}`, className)}
  >
    <Icon
      name={ICONS[type]}
      width={24}
      fill={ICON_COLOURS[type]}
      className='ds-banner__icon'
    />
    <div className='ds-banner__text'>
      {!!title && <div className='ds-banner__title'>{title}</div>}
      <div className='ds-banner__body'>{children}</div>
    </div>
    {!!action && <div className='ds-banner__action'>{action}</div>}
  </div>
)

export default Banner
