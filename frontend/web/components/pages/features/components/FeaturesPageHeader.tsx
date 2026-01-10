import React, { FC } from 'react'
import PageTitle from 'components/PageTitle'
import Button from 'components/base/forms/Button'
import Utils from 'common/utils/utils'
import Constants from 'common/constants'
import Permission from 'common/providers/Permission'

type FeaturesPageHeaderProps = {
  totalFeatures: number
  maxFeaturesAllowed: number | null
  onCreateFeature: () => void
  readOnly: boolean
  projectId: number
}

export const FeaturesPageHeader: FC<FeaturesPageHeaderProps> = ({
  maxFeaturesAllowed,
  onCreateFeature,
  projectId,
  readOnly,
  totalFeatures,
}) => {
  const featureLimitAlert = Utils.calculateRemainingLimitsPercentage(
    totalFeatures,
    maxFeaturesAllowed,
  )

  const featureLimitWarningBanner = featureLimitAlert.percentage
    ? Utils.displayLimitAlert('features', featureLimitAlert.percentage)
    : null

  return (
    <>
      {featureLimitWarningBanner}
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
