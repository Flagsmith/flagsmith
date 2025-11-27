import React, { FC } from 'react'
import PageTitle from 'components/PageTitle'
import Constants from 'common/constants'

type FeaturesPageHeaderProps = {
  totalFeatures: number
  maxFeaturesAllowed: number | null
  showCreateButton: boolean
  onCreateFeature: () => void
  readOnly: boolean
  createFeaturePermission: (
    el: (permission: boolean) => React.ReactNode,
  ) => React.ReactNode
}

export const FeaturesPageHeader: FC<FeaturesPageHeaderProps> = ({
  createFeaturePermission,
  maxFeaturesAllowed,
  onCreateFeature,
  readOnly,
  showCreateButton,
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
          <>
            {showCreateButton
              ? createFeaturePermission((perm) => (
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
                ))
              : null}
          </>
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
