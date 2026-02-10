import React, { FC } from 'react'
import InfoMessage from 'components/InfoMessage'
import Button from 'components/base/forms/Button'
import ModalHR from 'components/modals/ModalHR'

type FeatureUpdateSummaryProps = {
  identity?: string
  onCreateFeature: () => void
  isSaving: boolean
  name: string
  invalid: boolean
  regexValid: boolean
  featureLimitPercentage: number
  hasMetadataRequired: boolean
}

const FeatureUpdateSummary: FC<FeatureUpdateSummaryProps> = ({
  featureLimitPercentage,
  hasMetadataRequired,
  identity,
  invalid,
  isSaving,
  name,
  onCreateFeature,
  regexValid,
}) => {
  return (
    <>
      <ModalHR className={`my-4 ${identity ? 'mx-3' : ''}`} />
      {!identity && (
        <div className='text-right mb-3'>
          <InfoMessage collapseId={'create-flag'}>
            This will create the feature for <strong>all environments</strong>,
            you can edit this feature per environment once the feature is
            created.
          </InfoMessage>

          <Button
            onClick={onCreateFeature}
            data-test='create-feature-btn'
            id='create-feature-btn'
            disabled={
              isSaving ||
              !name ||
              invalid ||
              !regexValid ||
              featureLimitPercentage >= 100 ||
              hasMetadataRequired
            }
          >
            {isSaving ? 'Creating' : 'Create Feature'}
          </Button>
        </div>
      )}
    </>
  )
}

export default FeatureUpdateSummary
