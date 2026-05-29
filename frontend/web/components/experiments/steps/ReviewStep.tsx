import { FC } from 'react'
import { ProjectFlag } from 'common/types/responses'
import Button from 'components/base/forms/Button'
import ContentCard from 'components/base/grid/ContentCard'
import VariationTable from 'components/experiments/VariationTable'
import './ReviewStep.scss'

type ReviewStepProps = {
  name: string
  hypothesis: string
  selectedFeature: ProjectFlag | null
  onEditSetup: () => void
}

const ReviewStep: FC<ReviewStepProps> = ({
  hypothesis,
  name,
  onEditSetup,
  selectedFeature,
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
                selectedFeature.initial_value?.toString() ??
                ''
              }
              variations={selectedFeature.multivariate_options}
            />
          </>
        )}
      </ContentCard>
    </div>
  )
}

export default ReviewStep
