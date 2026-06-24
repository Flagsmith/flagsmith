import { FC, useMemo } from 'react'
import ContentCard from 'components/base/grid/ContentCard'
import ColorSwatch from 'components/ColorSwatch'
import { Experiment, ExpectedDirection } from 'common/types/responses'
import { getPrimaryMetric } from 'components/experiments/constants'
import { getVariantIdentities } from './derive'
import './results.scss'

const EXPECTED_DIRECTION_CHIP: Record<ExpectedDirection, string> = {
  decrease: '↓ should decrease',
  increase: '↑ should increase',
  not_decrease: 'should not decrease',
  not_increase: 'should not increase',
}

type ExperimentConfigurationProps = {
  experiment: Experiment
}

const ExperimentConfiguration: FC<ExperimentConfigurationProps> = ({
  experiment,
}) => {
  const metric = getPrimaryMetric(experiment)
  const identities = useMemo(
    () => getVariantIdentities(experiment.feature),
    [experiment.feature],
  )

  const treatmentTotal = (experiment.feature.multivariate_options ?? []).reduce(
    (sum, mv) => sum + mv.default_percentage_allocation,
    0,
  )

  const getAllocation = (index: number): number =>
    index === 0
      ? 100 - treatmentTotal
      : experiment.feature.multivariate_options?.[index - 1]
          ?.default_percentage_allocation ?? 0

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
        <ContentCard compact title='Variation Split'>
          <div className='d-flex flex-column gap-2'>
            {identities.map((v, i) => (
              <div
                key={v.key}
                className='d-flex align-items-center justify-content-between'
              >
                <span className='d-flex align-items-center gap-2'>
                  <ColorSwatch color={v.colour} size='sm' shape='circle' />
                  <span>{v.name}</span>
                </span>
                <span className='text-muted'>
                  {Math.round(getAllocation(i))}%
                </span>
              </div>
            ))}
          </div>
        </ContentCard>
      </div>
    </div>
  )
}

export default ExperimentConfiguration
