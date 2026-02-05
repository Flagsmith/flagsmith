import React, { FC, useState } from 'react'
import PageTitle from 'components/PageTitle'
import Button from 'components/base/forms/Button'
import Constants from 'common/constants'
import Permission from 'common/providers/Permission'
import FeatureLimitAlert from 'components/modals/create-feature/FeatureLimitAlert'

type FeaturesPageHeaderProps = {
  onCreateFeature: () => void
  readOnly: boolean
  projectId: number
}

export const FeaturesPageHeader: FC<FeaturesPageHeaderProps> = ({
  onCreateFeature,
  projectId,
  readOnly,
}) => {
  const [featureLimitAlert, setFeatureLimitAlert] = useState({
    limit: 0,
    percentage: 0,
  })

  return (
    <>
      <FeatureLimitAlert
        projectId={projectId}
        onChange={setFeatureLimitAlert}
      />
      <PageTitle
        title={'Features'}
        cta={
          <Permission
            level='project'
            permission='CREATE_FEATURE'
            id={projectId}
            showTooltip
            permissionName='Create Feature'
          >
            {({ permission: perm }) => (
              <Button
                disabled={
                  !perm || readOnly || featureLimitAlert.percentage >= 100
                }
                className='w-100'
                data-test='show-create-feature-btn'
                id='show-create-feature-btn'
                onClick={onCreateFeature}
              >
                Create Feature
              </Button>
            )}
          </Permission>
        }
      >
        View and manage{' '}
        <Tooltip
          title={
            <Button className='fw-normal' theme='text'>
              feature flags
            </Button>
          }
          place='right'
        >
          {Constants.strings.FEATURE_FLAG_DESCRIPTION}
        </Tooltip>{' '}
        and{' '}
        <Tooltip
          title={
            <Button className='fw-normal' theme='text'>
              remote config
            </Button>
          }
          place='right'
        >
          {Constants.strings.REMOTE_CONFIG_DESCRIPTION}
        </Tooltip>{' '}
        for your selected environment.
      </PageTitle>
    </>
  )
}
