import React, { FC } from 'react'
import InfoMessage from 'components/InfoMessage'
import Button from 'components/base/forms/Button'
import ModalHR from 'components/modals/ModalHR'
import { useGetProjectQuery } from 'common/services/useProject'

type FeatureUpdateSummaryProps = {
  identity?: string
  projectId: number | string
  onCreateFeature: () => void
  isSaving: boolean
  name: string
  invalid: boolean
  regexValid: boolean
  featureLimitPercentage: number
  hasMetadataRequired: boolean
  ownerIds?: number[]
  groupOwnerIds?: number[]
}

const FeatureUpdateSummary: FC<FeatureUpdateSummaryProps> = ({
  featureLimitPercentage,
  groupOwnerIds,
  hasMetadataRequired,
  identity,
  invalid,
  isSaving,
  name,
  onCreateFeature,
  ownerIds,
  projectId,
  regexValid,
}) => {
  const { data: project } = useGetProjectQuery(
    { id: parseInt(projectId as string, 10) },
    { skip: !projectId },
  )
  const preventFlagDefaults = !!project?.prevent_flag_defaults
  const enforceOwners = !!project?.enforce_feature_owners
  const hasOwners =
    (ownerIds?.length ?? 0) > 0 || (groupOwnerIds?.length ?? 0) > 0
  const missingRequiredOwners = enforceOwners && !hasOwners

  return (
    <>
      <ModalHR className={`my-4 ${identity ? 'mx-3' : ''}`} />
      {!identity && (
        <div className='text-right mb-3'>
          {!preventFlagDefaults && (
            <InfoMessage collapseId={'create-flag'}>
              This will create the feature for <strong>all environments</strong>
              , you can edit this feature per environment once the feature is
              created.
            </InfoMessage>
          )}

          {missingRequiredOwners && (
            <InfoMessage>
              This project requires at least one user or group owner to be
              assigned when creating a feature. Please assign an owner in the
              settings above.
            </InfoMessage>
          )}

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
              hasMetadataRequired ||
              missingRequiredOwners
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
