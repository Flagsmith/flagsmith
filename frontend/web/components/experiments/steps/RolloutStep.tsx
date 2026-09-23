import { FC } from 'react'
import { ExperimentAudienceMatch, ProjectFlag } from 'common/types/responses'
import Button from 'components/base/forms/Button'
import ContentCard from 'components/base/grid/ContentCard'
import AudiencePicker from 'components/experiments/AudiencePicker'
import RolloutSlider from 'components/experiments/RolloutSlider'
import RolloutSplitEditor from 'components/experiments/RolloutSplitEditor'
import RolloutSummary from 'components/experiments/RolloutSummary'
import {
  AudienceSegment,
  VariationSplitEntry,
  getEvenSplit,
} from 'components/experiments/rollout'

type RolloutStepProps = {
  selectedFeature: ProjectFlag | null
  projectId: number
  environmentId: string
  rolloutPercentage: number
  variationSplit: VariationSplitEntry[]
  audienceSegments: AudienceSegment[]
  audienceMatch: ExperimentAudienceMatch
  onRolloutChange: (value: number) => void
  onSplitChange: (entries: VariationSplitEntry[]) => void
  onAudienceSegmentsChange: (segments: AudienceSegment[]) => void
  onAudienceMatchChange: (match: ExperimentAudienceMatch) => void
}

const RolloutStep: FC<RolloutStepProps> = ({
  audienceMatch,
  audienceSegments,
  environmentId,
  onAudienceMatchChange,
  onAudienceSegmentsChange,
  onRolloutChange,
  onSplitChange,
  projectId,
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
    <div className='d-flex flex-column gap-4 mx-0'>
      <ContentCard
        background='white'
        title='Targeted audience'
        description='Limit the experiment to identities in a segment. The segment rules are copied when the experiment starts, so later edits to the segment leave the experiment untouched.'
      >
        <AudiencePicker
          projectId={projectId}
          environmentId={environmentId}
          segments={audienceSegments}
          match={audienceMatch}
          onSegmentsChange={onAudienceSegmentsChange}
          onMatchChange={onAudienceMatchChange}
        />
      </ContentCard>

      <ContentCard
        background='white'
        title='Rollout'
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
            id='experiment-wizard-rollout-split-evenly'
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
        audience={{ match: audienceMatch, segments: audienceSegments }}
      />
    </div>
  )
}

export default RolloutStep
