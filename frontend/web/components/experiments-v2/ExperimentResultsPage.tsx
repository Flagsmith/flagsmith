import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import StatusBadge from './shared/StatusBadge'
import ExperimentStatCard from './shared/ExperimentStatCard'
import MetricsComparisonTable from './shared/MetricsComparisonTable'
import { MOCK_EXPERIMENT_RESULT } from './types'
import './ExperimentResultsPage.scss'

const ExperimentResultsPage: FC = () => {
  const result = MOCK_EXPERIMENT_RESULT

  return (
    <div className='experiment-results-page'>
      <div className='experiment-results-page__header'>
        <div className='experiment-results-page__title-row'>
          <h1 className='experiment-results-page__title'>{result.name}</h1>
          <StatusBadge status={result.status} />
          <span className='experiment-results-page__days'>
            Day {result.daysCurrent} of {result.daysTotal}
          </span>
        </div>

        <div className='experiment-results-page__action-row'>
          <span className='experiment-results-page__subtitle'>
            Primary metric: {result.primaryMetric} &middot; Last updated{' '}
            {result.lastUpdated}
          </span>
          <div className='experiment-results-page__actions'>
            <Button
              theme='outline'
              size='small'
              iconLeft='open-external-link'
              iconSize={14}
            >
              Export
            </Button>
            <Button theme='danger' size='small'>
              Stop Experiment
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

      <div className='experiment-results-page__table-section'>
        <h2 className='experiment-results-page__section-title'>
          Metrics Comparison
        </h2>
        <MetricsComparisonTable metrics={result.metrics} />
      </div>
    </div>
  )
}

ExperimentResultsPage.displayName = 'ExperimentResultsPage'
export default ExperimentResultsPage
