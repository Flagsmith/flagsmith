import React from 'react'
import Setting from 'components/Setting'
import { Organisation } from 'common/types/responses'
import { useUpdateOrganisationWithToast } from 'components/pages/organisation-settings/hooks'

type Force2FASettingProps = {
  organisation: Organisation
}

export const Force2FASetting = ({ organisation }: Force2FASettingProps) => {
  const [updateOrganisationWithToast, { isLoading: isSaving }] =
    useUpdateOrganisationWithToast()

  const handleToggle = async () => {
    await updateOrganisationWithToast(
      {
        force_2fa: !organisation.force_2fa,
      },
      organisation.id,
    )
  }

  return (
    <Setting
      feature='FORCE_2FA'
      data-test='js-force-2fa'
      disabled={isSaving}
      onChange={handleToggle}
      checked={organisation.force_2fa}
    />
  )
}
