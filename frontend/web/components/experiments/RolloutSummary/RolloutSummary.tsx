import { FC } from 'react'
import { ProjectFlag } from 'common/types/responses'
import Icon from 'components/icons/Icon'
import DistributionBar from 'components/experiments/DistributionBar'
import {
  VariationSplitEntry,
  getRolloutSummaryRows,
  getTrafficSegments,
} from 'components/experiments/rollout'
import './RolloutSummary.scss'

type RolloutSummaryProps = {
  selectedFeature: ProjectFlag
  rolloutPercentage: number
  variationSplit: VariationSplitEntry[]
}

const formatPercentage = (value: number): string =>
  `${Number(value.toFixed(1))}%`

const RolloutSummary: FC<RolloutSummaryProps> = ({
  rolloutPercentage,
  selectedFeature,
  variationSplit,
}) => {
  const rows = getRolloutSummaryRows(selectedFeature, variationSplit)
  const arms = getTrafficSegments(
    selectedFeature,
    variationSplit,
    rolloutPercentage,
  )
    .map((segment, index) => ({
      colour: segment.colour,
      label: segment.label,
      scaled: segment.percentage,
      weight: rows[index]?.percentage ?? 0,
    }))
    .filter((arm) => arm.scaled > 0)
  const notReleased = Math.max(0, 100 - rolloutPercentage)

  const barSegments = [
    ...arms.map((arm) => ({
      colour: arm.colour,
      key: arm.label,
      weight: arm.scaled,
    })),
    { hatched: true, key: 'not-released', weight: notReleased },
  ]

  return (
    <div className='rollout-summary'>
      <div className='rollout-summary__header'>
        <span className='rollout-summary__title'>Rollout configuration</span>
        <span className='rollout-summary__not-released'>
          <Icon name='eye-off' width={16} />
          Not released to {notReleased}%
        </span>
      </div>

      <DistributionBar segments={barSegments} />

      <div className='rollout-summary__legend'>
        {arms.map((arm) => (
          <div key={arm.label} className='rollout-summary__legend-item'>
            <span
              className='rollout-summary__legend-swatch'
              style={{ background: arm.colour }}
            />
            <span className='rollout-summary__legend-label'>{arm.label}</span>
            <span className='rollout-summary__legend-value'>
              {formatPercentage(arm.weight)}
            </span>
          </div>
        ))}
      </div>

      <div className='rollout-summary__note'>
        <Icon name='people' width={20} />
        <span>
          {rolloutPercentage}% of eligible identities enter the experiment.
          <br />
          Actual time-to-significance depends on traffic, baseline rate, and the
          lift you're trying to detect.
        </span>
      </div>
    </div>
  )
}

export default RolloutSummary
