import { FC } from 'react'
import { ProjectFlag } from 'common/types/responses'
import Panel from 'components/base/grid/Panel'

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
      <Panel
        title='Setup'
        action={
          <button
            type='button'
            className='btn btn-link text-primary p-0'
            onClick={onEditSetup}
          >
            Edit
          </button>
        }
      >
        <div className='d-flex justify-content-between py-2 border-bottom'>
          <span className='text-muted'>Name</span>
          <span>{name}</span>
        </div>
        <div className='py-2 border-bottom'>
          <div className='text-muted mb-1'>Hypothesis</div>
          <blockquote
            className='border-start border-3 ps-3 mb-0 text-muted'
            style={{ fontSize: 14 }}
          >
            {hypothesis}
          </blockquote>
        </div>
        {selectedFeature && (
          <>
            <div className='d-flex justify-content-between py-2 border-bottom'>
              <span className='text-muted'>Feature Flag</span>
              <span>{selectedFeature.name}</span>
            </div>
            <div className='py-2'>
              <div className='d-flex align-items-center py-1'>
                <span
                  className='d-inline-block rounded-circle me-2'
                  style={{
                    backgroundColor: 'var(--success)',
                    height: 10,
                    width: 10,
                  }}
                />
                <span className='flex-fill'>Control</span>
                <code>{selectedFeature.initial_value}</code>
              </div>
              {selectedFeature.multivariate_options.map((mv) => (
                <div key={mv.id} className='d-flex align-items-center py-1'>
                  <span
                    className='d-inline-block rounded-circle me-2'
                    style={{
                      backgroundColor: 'var(--primary)',
                      height: 10,
                      width: 10,
                    }}
                  />
                  <span className='flex-fill'>
                    {mv.string_value || `Variation ${mv.id}`}
                  </span>
                  <code>{getVariationValue(mv)}</code>
                </div>
              ))}
            </div>
          </>
        )}
      </Panel>
    </div>
  )
}

export default ReviewStep
