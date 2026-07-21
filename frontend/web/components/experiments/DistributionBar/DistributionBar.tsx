import { FC } from 'react'
import cn from 'classnames'
import './DistributionBar.scss'

export type DistributionBarSegment = {
  key: string
  weight: number
  colour?: string
  hatched?: boolean
}

type DistributionBarProps = {
  segments: DistributionBarSegment[]
  className?: string
}

const DistributionBar: FC<DistributionBarProps> = ({ className, segments }) => (
  <div className={cn('distribution-bar', className)}>
    {segments.map((segment) =>
      segment.weight > 0 ? (
        <div
          key={segment.key}
          className={cn('distribution-bar__segment', {
            'distribution-bar__segment--hatched': segment.hatched,
          })}
          style={{
            background: segment.hatched ? undefined : segment.colour,
            width: `${segment.weight}%`,
          }}
        />
      ) : null,
    )}
  </div>
)

export default DistributionBar
