import { FC } from 'react'
import './UsageBarThresholds.scss'

export type UsageBarThresholdsProps = {
  thresholds: number[]
}

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
