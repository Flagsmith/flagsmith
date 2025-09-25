import React from 'react'
import AccountStore from 'common/stores/account-store'
import Button from 'components/base/forms/Button'

interface EmptyFeatureHealthProvidersProps {
  projectId: number
}

const EmptyFeatureHealthProviders: React.FC<
  EmptyFeatureHealthProvidersProps
> = ({ projectId }) => {
  const isAdmin = AccountStore.isAdmin()

  const learnMoreButton = (
    <Button
      theme='text'
      href='https://docs.flagsmith.com/advanced-use/feature-health'
      target='_blank'
      rel='noreferrer'
      className='fw-normal ml-1'
    >
      Learn more.
    </Button>
  )

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
              to start monitoring your feature health.{''}
              {learnMoreButton}
            </p>
          ) : (
            <p>
              Contact your Flagsmith administrators to configure a feature
              health provider.
              {learnMoreButton}
            </p>
          )}
        </div>
      </div>
    </>
  )
}

export default EmptyFeatureHealthProviders
