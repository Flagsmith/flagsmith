import React, { FC } from 'react'
import FeatureSettings from './tabs/FeatureSettings'
import JSONReference from 'components/JSONReference'
import ModalHR from 'components/modals/ModalHR'
import Button from 'components/base/forms/Button'
import { ProjectFlag } from 'common/types/responses'

type SettingsTabContentProps = {
  projectId: number
  projectFlag: ProjectFlag
  projectAdmin: boolean
  createFeature: boolean
  featureContentType: Record<string, any>
  identity?: string
  isEdit: boolean
  isSaving: boolean
  invalid: boolean
  hasMetadataRequired: boolean
  onChange: (changes: Partial<ProjectFlag>) => void
  onHasMetadataRequiredChange: (required: boolean) => void
  onSaveSettings: () => void
}

const SettingsTabContent: FC<SettingsTabContentProps> = ({
  createFeature,
  featureContentType,
  hasMetadataRequired,
  identity,
  invalid,
  isEdit,
  isSaving,
  onChange,
  onHasMetadataRequiredChange,
  onSaveSettings,
  projectAdmin,
  projectFlag,
  projectId,
}) => {
  return (
    <>
      <FeatureSettings
        projectAdmin={projectAdmin}
        createFeature={createFeature}
        featureContentType={featureContentType}
        identity={identity}
        isEdit={isEdit}
        projectId={projectId}
        projectFlag={projectFlag}
        onChange={onChange}
        onHasMetadataRequiredChange={onHasMetadataRequiredChange}
      />
      <JSONReference
        className='mb-3'
        showNamesButton
        title={'Feature'}
        json={projectFlag}
      />
      <ModalHR className='mt-4' />
      {isEdit && (
        <div className='text-right mt-3'>
          {!!createFeature && (
            <>
              <p className='text-right modal-caption fs-small lh-sm'>
                This will save the above settings{' '}
                <strong>all environments</strong>.
              </p>
              <Button
                onClick={onSaveSettings}
                data-test='update-feature-btn'
                id='update-feature-btn'
                disabled={
                  isSaving ||
                  !projectFlag.name ||
                  invalid ||
                  hasMetadataRequired
                }
              >
                {isSaving ? 'Updating' : 'Update Settings'}
              </Button>
            </>
          )}
        </div>
      )}
    </>
  )
}

export default SettingsTabContent
