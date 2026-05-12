import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import StatusBadge from './shared/StatusBadge'
import ExperimentStatCard from './shared/ExperimentStatCard'
import MetricsComparisonTable from './shared/MetricsComparisonTable'
import MetricsTrendChart from './shared/MetricsTrendChart'
import { MOCK_EXPERIMENT_RESULT } from './types'
import './ExperimentResultsPage.scss'

const formatTargeting = (conditions: string[]): string =>
  conditions.length === 0 ? 'All identities' : conditions.join(' AND ')

const ExperimentResultsPage: FC = () => {
  const result = MOCK_EXPERIMENT_RESULT
  const { config } = result

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
            <Button
              theme='danger'
              size='small'
              title='Conclude this experiment and choose which variant to keep'
            >
              End Experiment
            </Button>
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
            {result.winningVariation} is outperforming Control with{' '}
            {result.probabilityToBest}% probability of being the best variant.
            Consider concluding the experiment and rolling{' '}
            {result.winningVariation} out to 100% of traffic.
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

      {/* Experiment config summary — mirrors the wizard's Setup + Audience steps */}
      <div className='experiment-results-page__config'>
        <h2 className='experiment-results-page__section-title'>
          Experiment Configuration
        </h2>
        <div className='experiment-results-page__config-grid'>
          <div className='experiment-results-page__config-item'>
            <span className='experiment-results-page__config-label'>
              Feature Flag
            </span>
            <span className='experiment-results-page__config-value experiment-results-page__config-value--mono'>
              {config.featureFlag}
            </span>
          </div>
          <div className='experiment-results-page__config-item'>
            <span className='experiment-results-page__config-label'>
              Targeting
            </span>
            <span className='experiment-results-page__config-value'>
              {formatTargeting(config.targeting)}
            </span>
          </div>
          <div className='experiment-results-page__config-item'>
            <span className='experiment-results-page__config-label'>
              Sample Size
            </span>
            <span className='experiment-results-page__config-value'>
              {config.samplePercentage}% of eligible users
            </span>
          </div>
          <div className='experiment-results-page__config-item'>
            <span className='experiment-results-page__config-label'>
              Variation Split
            </span>
            <div className='experiment-results-page__split'>
              {config.arms.map((arm) => (
                <div
                  key={arm.label}
                  className='experiment-results-page__split-arm'
                >
                  <span
                    className='experiment-results-page__split-swatch'
                    style={{ background: arm.colour }}
                  />
                  <span className='experiment-results-page__split-label'>
                    {arm.label}
                  </span>
                  <span className='experiment-results-page__split-weight'>
                    {arm.weight}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

ExperimentResultsPage.displayName = 'ExperimentResultsPage'
export default ExperimentResultsPage
