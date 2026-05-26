import { FC, useMemo } from 'react'
import { ProjectFlag } from 'common/types/responses'
import { useGetFeatureListQuery } from 'common/services/useProjectFlag'
import { useProjectEnvironments } from 'common/hooks/useProjectEnvironments'
import useDebouncedSearch from 'common/useDebouncedSearch'
import Utils from 'common/utils/utils'
import ContentCard from 'components/base/grid/ContentCard'
import 'components/experiments/wizard.scss'

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
      },
      { skip: !numericEnvId },
    )

  const multivariateFeatures = useMemo(() => {
    if (!featureList?.results) return []
    return featureList.results.filter((f) => f.type === 'MULTIVARIATE')
  }, [featureList])

  const getVariationValue = (
    mv: ProjectFlag['multivariate_options'][number],
  ) => {
    if (mv.type === 'unicode') return mv.string_value
    if (mv.type === 'int') return String(mv.integer_value ?? '')
    if (mv.type === 'bool') return String(mv.boolean_value ?? '')
    return ''
  }

  return (
    <div className='d-flex flex-column gap-4'>
      <ContentCard title='Experiment details'>
        <p className='text-muted fs-small mb-0'>
          Name the experiment and capture what you&apos;re trying to learn
          before picking a flag.
        </p>

        <div className='wizard-field'>
          <label className='wizard-field__label'>
            Experiment Name <span className='wizard-field__required'>*</span>
          </label>
          <Input
            value={name}
            onChange={(e: InputEvent) =>
              onNameChange(Utils.safeParseEventValue(e))
            }
            placeholder='e.g. Checkout Button Redesign'
          />
        </div>

        <div className='wizard-field'>
          <label className='wizard-field__label'>
            Hypothesis <span className='wizard-field__required'>*</span>
          </label>
          <textarea
            className='wizard-field__textarea'
            rows={3}
            value={hypothesis}
            onChange={(e) => onHypothesisChange(e.target.value)}
            placeholder='e.g. Redesigning the checkout button with a clearer CTA will increase conversion rates by at least 15% within 30 days'
          />
          <span className='wizard-field__hint'>
            A good hypothesis names the change, the metric, the expected
            magnitude, and the timeframe.
          </span>
        </div>
      </ContentCard>

      <ContentCard title='Feature flag'>
        <p className='text-muted fs-small mb-0'>
          The flag you&apos;re experimenting on. Variations are read-only
          &mdash; they&apos;re defined on the flag itself.
        </p>

        <div className='wizard-field'>
          <label className='wizard-field__label'>Feature Flag</label>
          <Select
            value={
              selectedFeature
                ? { label: selectedFeature.name, value: selectedFeature.id }
                : null
            }
            options={multivariateFeatures.map((f) => ({
              label: f.name,
              value: f.id,
            }))}
            onInputChange={(val: string) => setSearchInput(val)}
            onChange={(option: { label: string; value: number } | null) => {
              if (option) {
                const feature = multivariateFeatures.find(
                  (f) => f.id === option.value,
                )
                if (feature) onFeatureSelect(feature)
              }
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
            <table className='table table-sm mb-0'>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Value</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>
                    <span
                      className='d-inline-block rounded-circle me-2'
                      style={{
                        backgroundColor: 'var(--success)',
                        height: 10,
                        width: 10,
                      }}
                    />
                    Control
                    <span className='badge bg-light text-muted ms-2'>
                      control
                    </span>
                  </td>
                  <td>
                    <code>{selectedFeature.initial_value}</code>
                  </td>
                </tr>
                {selectedFeature.multivariate_options.map((mv) => (
                  <tr key={mv.id}>
                    <td>
                      <span
                        className='d-inline-block rounded-circle me-2'
                        style={{
                          backgroundColor: 'var(--primary)',
                          height: 10,
                          width: 10,
                        }}
                      />
                      {mv.string_value || `Variation ${mv.id}`}
                    </td>
                    <td>
                      <code>{getVariationValue(mv)}</code>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </ContentCard>
    </div>
  )
}

export default SetupStep
