import { ChangeEvent, FC, useMemo } from 'react'
import { ProjectFlag } from 'common/types/responses'
import { useGetExperimentsQuery } from 'common/services/useExperiment'
import { useGetFeatureListQuery } from 'common/services/useProjectFlag'
import { useProjectEnvironments } from 'common/hooks/useProjectEnvironments'
import useDebouncedSearch from 'common/useDebouncedSearch'
import Utils from 'common/utils/utils'
import InputGroup from 'components/base/forms/InputGroup'
import ContentCard from 'components/base/grid/ContentCard'
import VariationTable from 'components/experiments/VariationTable'
import './SetupStep.scss'

type SetupStepProps = {
  name: string
  hypothesis: string
  selectedFeature: ProjectFlag | null
  projectId: number
  environmentId: string
  onNameChange: (name: string) => void
  onHypothesisChange: (hypothesis: string) => void
  onFeatureSelect: (feature: ProjectFlag) => void
}

const SetupStep: FC<SetupStepProps> = ({
  environmentId,
  hypothesis,
  name,
  onFeatureSelect,
  onHypothesisChange,
  onNameChange,
  projectId,
  selectedFeature,
}) => {
  const { search, setSearchInput } = useDebouncedSearch('')
  const { getEnvironmentIdFromKey } = useProjectEnvironments(projectId)
  const numericEnvId = getEnvironmentIdFromKey(environmentId)

  const { data: featureList, isLoading: isFeaturesLoading } =
    useGetFeatureListQuery(
      {
        environmentId: String(numericEnvId ?? ''),
        page: 1,
        page_size: 50,
        projectId,
        search: search || undefined,
        type: 'MULTIVARIATE',
      },
      { skip: !numericEnvId },
    )

  const multivariateFeatures = featureList?.results ?? []

  const { data: experimentsData } = useGetExperimentsQuery(
    { environmentId, page: 1, page_size: 100 },
    { skip: !environmentId },
  )
  const featureIdsInExperiment = useMemo(() => {
    const ids = new Set<number>()
    experimentsData?.results?.forEach((experiment) => {
      if (experiment.status !== 'completed' && experiment.feature?.id) {
        ids.add(experiment.feature.id)
      }
    })
    return ids
  }, [experimentsData])

  return (
    <div className='d-flex flex-column gap-4'>
      <ContentCard
        background='white'
        title='Experiment details'
        description="Name the experiment and capture what you're trying to learn before picking a flag."
      >
        <InputGroup
          title='Experiment Name *'
          value={name}
          onChange={(e: ChangeEvent<HTMLInputElement>) =>
            onNameChange(Utils.safeParseEventValue(e))
          }
          placeholder='e.g. Checkout Button Redesign'
          noMargin
        />

        <div>
          <InputGroup
            title='Hypothesis *'
            textarea
            inputProps={{ rows: 3 }}
            value={hypothesis}
            onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
              onHypothesisChange(Utils.safeParseEventValue(e))
            }
            placeholder='e.g. Redesigning the checkout button with a clearer CTA will increase conversion rates by at least 15% within 30 days'
            noMargin
          />
          <span className='wizard-field__hint'>
            A good hypothesis names the change, the metric, the expected
            magnitude, and the timeframe.
          </span>
        </div>
      </ContentCard>

      <ContentCard
        background='white'
        title='Feature flag'
        description="The flag you're experimenting on. Variations are read-only, defined on the flag itself."
      >
        <div className='wizard-field'>
          <label className='wizard-field__label'>Feature Flag</label>
          <Select
            value={
              selectedFeature
                ? { label: selectedFeature.name, value: selectedFeature.id }
                : null
            }
            options={multivariateFeatures.map((f) => {
              const isInExperiment = featureIdsInExperiment.has(f.id)
              return {
                feature: f,
                isDisabled: isInExperiment,
                label: isInExperiment
                  ? `${f.name} (already in an experiment)`
                  : f.name,
                value: f.id,
              }
            })}
            onInputChange={(val: string) => setSearchInput(val)}
            onChange={(
              option: {
                feature: ProjectFlag
                label: string
                value: number
              } | null,
            ) => {
              if (option) onFeatureSelect(option.feature)
            }}
            isLoading={isFeaturesLoading}
            placeholder='Search for a multivariate feature...'
            isClearable={false}
          />
          <span className='wizard-field__hint'>
            Only multi-variant flags can be experimented on.
          </span>
        </div>

        {selectedFeature && selectedFeature.multivariate_options.length > 0 && (
          <div className='wizard-field'>
            <label className='wizard-field__label'>Variations</label>
            <VariationTable
              controlValue={
                selectedFeature.environment_feature_state?.feature_state_value?.toString() ??
                ''
              }
              variations={selectedFeature.multivariate_options}
            />
          </div>
        )}
      </ContentCard>
    </div>
  )
}

export default SetupStep
