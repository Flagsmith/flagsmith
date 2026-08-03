import { FC, ReactNode } from 'react'
import './UsageBadge.scss'

export type BadgeTone = 'success' | 'warning' | 'danger' | 'info' | 'neutral'

type UsageBadgeProps = {
  tone: BadgeTone
  children: ReactNode
  /** Off for value-like badges, e.g. "Estimate". */
  withDot?: boolean
}

/**
 * PROTOTYPE (#8184). The dot-and-label badge from `experiments/StatusBadge`,
 * with a tone instead of an experiment status.
 *
 * If this shape is becoming the standard, the production move is to generalise
 * that component rather than keep two, which belongs with #8185.
 */
const UsageBadge: FC<UsageBadgeProps> = ({
  children,
  tone,
  withDot = true,
}) => (
  <span className={`usage-badge usage-badge--${tone}`}>
    {withDot && <span className='usage-badge__dot' />}
    {children}
  </span>
)

export default UsageBadge
