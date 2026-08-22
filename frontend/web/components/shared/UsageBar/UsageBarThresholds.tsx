import { FC } from 'react'
import './UsageBarThresholds.scss'

export type UsageBarThresholdsProps = {
  /** Percentages to mark, e.g. the points usage is notified at. */
  thresholds: number[]
}

/**
 * Ticks above the track. The one at the limit is marked so its label can be
 * pulled back inside the container instead of overflowing the right edge.
 */
const UsageBarThresholds: FC<UsageBarThresholdsProps> = ({ thresholds }) => (
  <>
    {thresholds.map((threshold) => {
      const atLimit = threshold >= 100

      return (
        <span
          key={threshold}
          className={
            atLimit
              ? 'usage-bar__marker usage-bar__marker--end'
              : 'usage-bar__marker'
          }
          style={{ left: `${threshold}%` }}
        >
          <span
            className={`usage-bar__marker-label fs-captionXSmall fw-semibold text-${
              atLimit ? 'danger' : 'warning'
            }`}
          >
            Notify {threshold}%
          </span>
        </span>
      )
    })}
  </>
)

export default UsageBarThresholds
