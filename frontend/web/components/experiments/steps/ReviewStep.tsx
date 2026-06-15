import { FC } from 'react'
import { ExpectedDirection, Metric, ProjectFlag } from 'common/types/responses'
import Button from 'components/base/forms/Button'
import ContentCard from 'components/base/grid/ContentCard'
import VariationTable from 'components/experiments/VariationTable'
import { getExpectedDirectionLabel } from 'components/experiments/constants'
import './ReviewStep.scss'

type ReviewStepProps = {
  name: string
  hypothesis: string
  selectedFeature: ProjectFlag | null
  selectedMetric: Metric | null
  expectedDirection: ExpectedDirection | null
  onEditSetup: () => void
  onEditMeasurement: () => void
}

const ReviewStep: FC<ReviewStepProps> = ({
  expectedDirection,
  hypothesis,
  name,
  onEditMeasurement,
  onEditSetup,
  selectedFeature,
  selectedMetric,
}) => {
  return (
    <div className='d-flex flex-column gap-4'>
      <ContentCard
        title='Setup'
        action={
          <Button theme='text' size='xSmall' onClick={onEditSetup}>
            Edit
          </Button>
        }
      >
        <div className='review-row review-row--block'>
          <span className='text-muted'>Name</span>
          <span className='review-row__value'>{name}</span>
        </div>
        {hypothesis && (
          <div className='review-row review-row--block'>
            <span className='text-muted'>Hypothesis</span>
            <span className='review-row__hypothesis'>{hypothesis}</span>
          </div>
        )}
        {selectedFeature && (
          <>
            <div className='review-row review-row--block'>
              <span className='text-muted'>Feature Flag</span>
              <span className='review-row__value review-row__value--flag'>
                {selectedFeature.name}
              </span>
            </div>
            <VariationTable
              controlValue={
                selectedFeature.environment_feature_state?.feature_state_value?.toString() ??
                ''
              }
              variations={selectedFeature.multivariate_options}
            />
          </>
        )}
      </ContentCard>

      <ContentCard
        title={selectedMetric ? 'Measurement (1 metric)' : 'Measurement'}
        action={
          <Button theme='text' size='xSmall' onClick={onEditMeasurement}>
            Edit
          </Button>
        }
      >
        {selectedMetric ? (
          <div className='review-metric-card'>
            <div className='review-metric-card__content'>
              <span className='review-metric-card__title'>
                {selectedMetric.name}
              </span>
              {!!selectedMetric.description && (
                <span className='review-metric-card__description'>
                  {selectedMetric.description}
                </span>
              )}
              {expectedDirection && (
                <span className='review-metric-card__direction'>
                  {getExpectedDirectionLabel(expectedDirection)}
                </span>
              )}
            </div>
            <span className='review-metric-card__badge'>Primary</span>
          </div>
        ) : (
          <p className='text-muted mb-0'>No metric selected.</p>
        )}
      </ContentCard>
    </div>
  )
}

export default ReviewStep
