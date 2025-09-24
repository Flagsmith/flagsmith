import React from 'react'
import AccountStore from 'common/stores/account-store'
import FeatureHealthProviderDocumentationNote from './FeatureHealthProviderDocumentationNote'

interface EmptyFeatureHealthProvidersProps {
  projectId: number
}

const EmptyFeatureHealthProviders: React.FC<
  EmptyFeatureHealthProvidersProps
> = ({ projectId }) => {
  const isAdmin = AccountStore.isAdmin()
  return (
    <>
      <h5 className='mb-4'>No Provider Configured</h5>
      <FeatureHealthProviderDocumentationNote defaultClosed={true} />
      <div className='d-flex flex-column gap-4'>
        <div className='text-center'>
          {isAdmin ? (
            <p>
              Configure a health provider in your{' '}
              <a
                className='fw-normal btn-link'
                href={`/project/${projectId}/settings?tab=feature-health`}
              >
                project settings
              </a>{' '}
              to start monitoring your feature health.
            </p>
          ) : (
            <p>
              Contact your Flagsmith administrators to configure a feature
              health provider.
            </p>
          )}
        </div>
      </div>
    </>
  )
}

export default EmptyFeatureHealthProviders
