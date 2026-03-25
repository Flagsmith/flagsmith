import React, { FC } from 'react'
import flagsmith from '@flagsmith/flagsmith'
import Project from 'common/project'
import FeatureAnalytics from 'components/feature-page/FeatureNavTab/FeatureAnalytics'
import FeatureCodeReferencesContainer from 'components/feature-page/FeatureNavTab/CodeReferences/FeatureCodeReferencesContainer'

type UsageTabProps = {
  projectId: number | string
  featureId: number
  environmentId: number
  hasCodeReferences: boolean
}

const UsageTab: FC<UsageTabProps> = ({
  environmentId,
  featureId,
  hasCodeReferences,
  projectId,
}) => {
  if (!projectId) {
    return null
  }
  return (
    <>
      {!Project.disableAnalytics && (
        <div className='mb-4'>
          <FeatureAnalytics
            projectId={`${projectId}`}
            featureId={`${featureId}`}
            defaultEnvironmentIds={[`${environmentId}`]}
          />
        </div>
      )}
      {hasCodeReferences && (
        <FormGroup className='mb-4'>
          <div className='d-flex align-items-center gap-2 mb-2'>
            <h5 className='mb-0'>Code references</h5>
            <span
              className='chip chip--xs bg-primary text-white'
              style={{ border: 'none' }}
            >
              New
            </span>
          </div>
          <div className='text-muted mb-2'>
            Code references allow you to track where feature flags are being
            used within your code.{' '}
            <a
              target='_blank'
              href='https://docs.flagsmith.com/managing-flags/code-references'
              rel='noreferrer'
              onClick={() => {
                flagsmith.trackEvent('code_references_click_docs', {
                  feature_id: featureId,
                })
              }}
            >
              Learn more
            </a>
          </div>
          <FeatureCodeReferencesContainer
            featureId={featureId}
            projectId={parseInt(`${projectId}`)}
          />
        </FormGroup>
      )}
    </>
  )
}

export default UsageTab
