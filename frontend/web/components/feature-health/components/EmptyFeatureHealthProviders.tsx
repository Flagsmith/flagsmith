import React from 'react'
import AccountStore from 'common/stores/account-store'

interface EmptyFeatureHealthProvidersProps {
  projectId: number
}

const DOCS_URL = 'https://docs.flagsmith.com/advanced-use/feature-health'

const EmptyFeatureHealthProviders: React.FC<
  EmptyFeatureHealthProvidersProps
> = ({ projectId }) => {
  const isAdmin = AccountStore.isAdmin()

  return (
    <FormGroup className='mb-4'>
      <h5 className='mb-2'>Health</h5>
      <p className='fs-small lh-sm mb-3'>
        Surface incidents, error rates and SLO breaches alongside this flag.
        Connect a health provider so the team can spot a flag that's making
        production worse and roll it back without leaving Flagsmith.{' '}
        <a
          target='_blank'
          rel='noreferrer'
          className='fw-normal btn-link'
          href={DOCS_URL}
        >
          Learn more
        </a>
        .
      </p>
      {isAdmin ? (
        <p className='fs-small lh-sm text-muted mb-0'>
          Configure a health provider in your{' '}
          <a
            target='_blank'
            rel='noreferrer'
            className='fw-normal btn-link'
            href={`/project/${projectId}/settings?tab=feature-health`}
          >
            project settings
          </a>{' '}
          to start monitoring this feature.
        </p>
      ) : (
        <p className='fs-small lh-sm text-muted mb-0'>
          Ask a project admin to configure a health provider in project
          settings.
        </p>
      )}
    </FormGroup>
  )
}

export default EmptyFeatureHealthProviders
