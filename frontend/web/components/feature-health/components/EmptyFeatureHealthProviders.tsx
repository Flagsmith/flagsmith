import React from 'react'
import AccountStore from 'common/stores/account-store'
import Link from 'components/base/link'

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
              <Link
                target='_blank'
                to={`/project/${projectId}/settings?tab=feature-health`}
              >
                project settings
              </Link>{' '}
              to start monitoring your feature health, or read about the
              functionality{' '}
              <Link
                target='_blank'
                href='https://docs.flagsmith.com/advanced-use/feature-health'
              >
                here
              </Link>
              .
            </p>
          ) : (
            <p>
              Contact your Flagsmith administrators to configure a feature
              health provider, or read about the functionality{' '}
              <Link
                target='_blank'
                href='https://docs.flagsmith.com/advanced-use/feature-health'
              >
                here
              </Link>
              .
            </p>
          )}
        </div>
      </div>
    </>
  )
}

export default EmptyFeatureHealthProviders
