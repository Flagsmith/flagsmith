import { FC } from 'react'
import { ProjectFlag } from 'common/types/responses'
import Button from 'components/base/forms/Button'
import ContentCard from 'components/base/grid/ContentCard'
import RolloutSlider from 'components/experiments/RolloutSlider'
import RolloutSplitEditor from 'components/experiments/RolloutSplitEditor'
import RolloutSummary from 'components/experiments/RolloutSummary'
import {
  VariationSplitEntry,
  getEvenSplit,
} from 'components/experiments/rollout'

type RolloutStepProps = {
  selectedFeature: ProjectFlag | null
  rolloutPercentage: number
  variationSplit: VariationSplitEntry[]
  onRolloutChange: (value: number) => void
  onSplitChange: (entries: VariationSplitEntry[]) => void
}

const RolloutStep: FC<RolloutStepProps> = ({
  onRolloutChange,
  onSplitChange,
  rolloutPercentage,
  selectedFeature,
  variationSplit,
}) => {
  if (!selectedFeature) {
    return (
      <ContentCard background='white' title='Rollout configuration'>
        <p className='text-muted mb-0'>
          Select a feature flag in the Setup step to configure the rollout.
        </p>
      </ContentCard>
    )
  }

  return (
    <div className='d-flex flex-column gap-4'>
      <ContentCard
        background='white'
        title='Sample Size'
        description='What percentage of eligible users enters the experiment?'
      >
        <RolloutSlider value={rolloutPercentage} onChange={onRolloutChange} />
      </ContentCard>

      <ContentCard
        background='white'
        title='Variation Split'
        description='Distribute sampled identities across control and treatment variations. Control takes one of the slots; weights must sum to 100.'
        action={
          <Button
            theme='outline'
            size='xSmall'
            onClick={() =>
              onSplitChange(getEvenSplit(selectedFeature.multivariate_options))
            }
          >
            Split evenly
          </Button>
        }
      >
        <RolloutSplitEditor
          multivariateOptions={selectedFeature.multivariate_options}
          variationSplit={variationSplit}
          onChange={onSplitChange}
        />
      </ContentCard>

      <RolloutSummary
        selectedFeature={selectedFeature}
        rolloutPercentage={rolloutPercentage}
        variationSplit={variationSplit}
      />
    </div>
  )
}

export default RolloutStep
