import React, { FC } from 'react'
import Utils from 'common/utils/utils'
import Button from 'components/base/forms/Button'
import { EnvironmentPermission } from 'common/types/permissions.types'

type IdentitySaveFooterProps = {
  identityName?: string
  environmentName: string
  savePermission: boolean
  isSaving: boolean
  projectFlagName: string
  invalid: boolean | number
  onSave: () => void
}

const IdentitySaveFooter: FC<IdentitySaveFooterProps> = ({
  environmentName,
  identityName,
  invalid,
  isSaving,
  onSave,
  projectFlagName,
  savePermission,
}) => {
  return (
    <div className='pr-3'>
      <div className='mb-3 mt-4'>
        <p className='text-start ml-3 modal-caption fs-small lh-small'>
          This will update the feature value for the user{' '}
          <strong>{identityName}</strong> in
          <strong> {environmentName}.</strong>
          {' Any segment overrides for this feature will now be ignored.'}
        </p>
      </div>

      <div className='text-right mb-2'>
        {Utils.renderWithPermission(
          savePermission,
          EnvironmentPermission.UPDATE_FEATURE_STATE,
          <div>
            <Button
              onClick={onSave}
              data-test='update-feature-btn'
              id='update-feature-btn'
              disabled={
                !savePermission || isSaving || !projectFlagName || !!invalid
              }
            >
              {isSaving ? 'Updating' : 'Update Feature'}
            </Button>
          </div>,
        )}
      </div>
    </div>
  )
}

export default IdentitySaveFooter
