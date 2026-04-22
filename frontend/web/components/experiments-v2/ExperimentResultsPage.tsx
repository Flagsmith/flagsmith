import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import StatusBadge from './shared/StatusBadge'
import ExperimentStatCard from './shared/ExperimentStatCard'
import MetricsComparisonTable from './shared/MetricsComparisonTable'
import MetricsTrendChart from './shared/MetricsTrendChart'
import { MOCK_EXPERIMENT_RESULT } from './types'
import './ExperimentResultsPage.scss'

const ExperimentResultsPage: FC = () => {
  const result = MOCK_EXPERIMENT_RESULT
  const progressPercent = Math.round(
    (result.daysCurrent / result.daysTotal) * 100,
  )

  return (
    <div className='experiment-results-page'>
      <div className='experiment-results-page__header'>
        <div className='experiment-results-page__title-row'>
          <h1 className='experiment-results-page__title'>{result.name}</h1>
          <StatusBadge status={result.status} />
        </div>

        <div className='experiment-results-page__action-row'>
          <span className='experiment-results-page__subtitle'>
            Primary metric: {result.primaryMetric} &middot; Last updated{' '}
            {result.lastUpdated}
          </span>
          <div className='experiment-results-page__actions'>
            <Button theme='danger' size='small'>
              Stop Experiment
            </Button>
          </div>
        </div>

        {/* Timeline progress */}
        <div className='experiment-results-page__timeline'>
          <div className='experiment-results-page__timeline-header'>
            <span className='experiment-results-page__timeline-label'>
              Experiment Timeline
            </span>
            <span className='experiment-results-page__timeline-value'>
              Day {result.daysCurrent} of {result.daysTotal}
            </span>
          </div>
          <div className='experiment-results-page__timeline-track'>
            <div
              className='experiment-results-page__timeline-fill'
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      </div>

      <div className='experiment-results-page__cards'>
        <ExperimentStatCard
          label='Users Enrolled'
          value={result.usersEnrolled}
        />
        <ExperimentStatCard
          label='Winning Variation'
          value={result.winningVariation}
          trend='positive'
        />
        <ExperimentStatCard
          label='Probability to be Best'
          value={`${result.probabilityToBest}%`}
        />
        <ExperimentStatCard
          label='Lift vs Control'
          value={`+${result.liftVsControl}%`}
          trend='positive'
          subtitle='vs control group'
        />
      </div>

      {/* Recommendation callout */}
      <div className='experiment-results-page__recommendation'>
        <Icon name='checkmark-circle' width={20} />
        <div className='experiment-results-page__recommendation-content'>
          <span className='experiment-results-page__recommendation-title'>
            Recommendation
          </span>
          <span className='experiment-results-page__recommendation-text'>
            Treatment B is outperforming Control with 94.2% probability of being
            the best variant. Consider rolling out Treatment B to 100% of
            traffic after the experiment concludes on day {result.daysTotal}.
          </span>
        </div>
      </div>

      <div className='experiment-results-page__table-section'>
        <h2 className='experiment-results-page__section-title'>
          Metrics Comparison
        </h2>
        <MetricsComparisonTable metrics={result.metrics} />

        <h3 className='experiment-results-page__subsection-title'>
          Trend over time
        </h3>
        <MetricsTrendChart trends={result.metricTrends} />
      </div>

      {/* Experiment config summary */}
      <div className='experiment-results-page__config'>
        <h2 className='experiment-results-page__section-title'>
          Experiment Configuration
        </h2>
        <div className='experiment-results-page__config-grid'>
          <div className='experiment-results-page__config-item'>
            <span className='experiment-results-page__config-label'>Type</span>
            <span className='experiment-results-page__config-value'>
              A/B Test
            </span>
          </div>
          <div className='experiment-results-page__config-item'>
            <span className='experiment-results-page__config-label'>
              Feature Flag
            </span>
            <span className='experiment-results-page__config-value experiment-results-page__config-value--mono'>
              checkout_button_redesign
            </span>
          </div>
          <div className='experiment-results-page__config-item'>
            <span className='experiment-results-page__config-label'>
              Segments
            </span>
            <span className='experiment-results-page__config-value'>
              All Users
            </span>
          </div>
          <div className='experiment-results-page__config-item'>
            <span className='experiment-results-page__config-label'>
              Traffic
            </span>
            <span className='experiment-results-page__config-value'>
              50% / 50%
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

ExperimentResultsPage.displayName = 'ExperimentResultsPage'
export default ExperimentResultsPage
