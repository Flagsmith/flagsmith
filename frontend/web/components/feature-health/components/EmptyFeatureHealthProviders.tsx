import React from 'react'
import AccountStore from 'common/stores/account-store'

interface EmptyFeatureHealthProvidersProps {
  projectId: number
}

const EmptyFeatureHealthProviders: React.FC<
  EmptyFeatureHealthProvidersProps
> = ({ projectId }) => {
  const isAdmin = AccountStore.isAdmin()

  return (
    <>
      <div className='mb-4'>
        <h5>No Provider Configured</h5>
      </div>
      <div className='d-flex flex-column gap-4'>
        <div className='text-center'>
          {isAdmin ? (
            <p className='modal-caption fs-small lh-sm'>
              Configure a health provider in your{' '}
              <a
                target='_blank'
                rel='noreferrer'
                className='fw-normal btn-link'
                href={`/project/${projectId}/settings?tab=feature-health`}
              >
                project settings
              </a>{' '}
              to start monitoring your feature health, or read about the
              functionality{' '}
              <a
                target='_blank'
                rel='noreferrer'
                className='fw-normal btn-link'
                href='https://docs.flagsmith.com/advanced-use/feature-health'
              >
                here
              </a>
              .
            </p>
          ) : (
            <p>
              Contact your Flagsmith administrators to configure a feature
              health provider, or read about the functionality{' '}
              <a
                target='_blank'
                rel='noreferrer'
                className='fw-normal btn-link'
                href='https://docs.flagsmith.com/advanced-use/feature-health'
              >
                here
              </a>
              .
            </p>
          )}
        </div>
      </div>
    </>
  )
}

export default EmptyFeatureHealthProviders
