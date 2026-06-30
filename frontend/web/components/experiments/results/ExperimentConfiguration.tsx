import { FC } from 'react'
import ContentCard from 'components/base/grid/ContentCard'
import { Experiment, ExpectedDirection } from 'common/types/responses'
import { getPrimaryMetric } from 'components/experiments/constants'
import ExperimentRolloutCard from './ExperimentRolloutCard'
import './results.scss'

const EXPECTED_DIRECTION_CHIP: Record<ExpectedDirection, string> = {
  decrease: '↓ should decrease',
  increase: '↑ should increase',
  not_decrease: 'should not decrease',
  not_increase: 'should not increase',
}

type ExperimentConfigurationProps = {
  experiment: Experiment
  environmentId: string
}

const ExperimentConfiguration: FC<ExperimentConfigurationProps> = ({
  environmentId,
  experiment,
}) => {
  const metric = getPrimaryMetric(experiment)

  return (
    <div className='row g-3 mb-4'>
      <div className='col-md-4'>
        <ContentCard compact title='Feature flag'>
          <div>
            <span className='selectable-card__tag'>
              {experiment.feature.name}
            </span>
          </div>
        </ContentCard>
      </div>
      <div className='col-md-4'>
        <ContentCard compact title='Primary Metric'>
          {metric ? (
            <div>
              <div>{metric.metric_name}</div>
              <div className='mt-3'>
                <span className='selectable-card__tag'>
                  {EXPECTED_DIRECTION_CHIP[metric.expected_direction]}
                </span>
              </div>
            </div>
          ) : (
            <span className='text-muted'>—</span>
          )}
        </ContentCard>
      </div>
      <div className='col-md-4'>
        <ExperimentRolloutCard
          experiment={experiment}
          environmentId={environmentId}
        />
      </div>
    </div>
  )
}

export default ExperimentConfiguration
