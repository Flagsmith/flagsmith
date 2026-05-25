import { FC, useMemo } from 'react'
import { ProjectFlag } from 'common/types/responses'
import { useGetFeatureListQuery } from 'common/services/useProjectFlag'
import useDebouncedSearch from 'common/useDebouncedSearch'
import Utils from 'common/utils/utils'
import Panel from 'components/base/grid/Panel'

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

  const { data: featureList, isLoading: isFeaturesLoading } =
    useGetFeatureListQuery({
      environmentId,
      page: 1,
      page_size: 50,
      projectId,
      search: search || undefined,
    })

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
      <Panel title='Experiment details'>
        <p className='text-muted mb-3'>
          Name the experiment and capture what you&#39;re trying to learn before
          picking a flag.
        </p>
        <FormGroup className='mb-3'>
          <label className='fw-bold mb-1'>
            Experiment Name <span className='text-danger'>*</span>
          </label>
          <Input
            value={name}
            onChange={(e: InputEvent) =>
              onNameChange(Utils.safeParseEventValue(e))
            }
            placeholder='e.g. Checkout Button Redesign'
          />
        </FormGroup>
        <FormGroup>
          <label className='fw-bold mb-1'>
            Hypothesis <span className='text-danger'>*</span>
          </label>
          <textarea
            className='form-control'
            rows={4}
            value={hypothesis}
            onChange={(e) => onHypothesisChange(e.target.value)}
            placeholder='e.g. Redesigning the checkout button will increase conversion rates by at least 15% within 30 days'
          />
          <div className='text-muted mt-1' style={{ fontSize: 12 }}>
            A good hypothesis names the change, the metric, the expected
            magnitude, and the timeframe.
          </div>
        </FormGroup>
      </Panel>

      <Panel title='Feature flag'>
        <p className='text-muted mb-3'>
          The flag you&#39;re experimenting on. Variations are read-only &#8212;
          they&#39;re defined on the flag itself.
        </p>
        <FormGroup className='mb-2'>
          <label className='fw-bold mb-1'>Feature Flag</label>
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
            onChange={(option: { value: number; label: string } | null) => {
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
          <div className='text-muted mt-1' style={{ fontSize: 12 }}>
            Only multi-variant flags can be experimented on.
          </div>
        </FormGroup>

        {selectedFeature && selectedFeature.multivariate_options.length > 0 && (
          <div className='mt-3'>
            <label className='fw-bold mb-2'>Variations</label>
            <table className='table table-sm'>
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
      </Panel>
    </div>
  )
}

export default SetupStep
