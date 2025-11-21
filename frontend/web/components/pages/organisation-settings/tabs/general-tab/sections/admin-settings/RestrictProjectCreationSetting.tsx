import React from 'react'
import Setting from 'components/Setting'
import Utils from 'common/utils/utils'
import { Organisation } from 'common/types/responses'
import { useUpdateOrganisationWithToast } from 'components/pages/organisation-settings/hooks'

type RestrictProjectCreationSettingProps = {
  organisation: Organisation
}

export const RestrictProjectCreationSetting = ({
  organisation,
}: RestrictProjectCreationSettingProps) => {
  const [updateOrganisationWithToast, { isLoading: isSaving }] =
    useUpdateOrganisationWithToast()

  const hasFeature = Utils.getFlagsmithHasFeature(
    'restrict_project_create_to_admin',
  )

  const handleToggle = async () => {
    await updateOrganisationWithToast(
      {
        name: organisation.name,
        restrict_project_create_to_admin:
          !organisation.restrict_project_create_to_admin,
      },
      organisation.id,
    )
  }

  if (!hasFeature) {
    return null
  }

  return (
    <FormGroup className='mt-4'>
      <Setting
        title='Restrict Project Creation'
        description='Only allow organisation admins to create projects'
        data-test='js-restrict-project-creation'
        disabled={isSaving}
        onChange={handleToggle}
        checked={organisation.restrict_project_create_to_admin}
      />
    </FormGroup>
  )
}
