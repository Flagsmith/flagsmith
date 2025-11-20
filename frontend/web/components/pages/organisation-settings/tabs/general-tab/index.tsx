import React from 'react'
import { Organisation } from 'common/types/responses'
import JSONReference from 'components/JSONReference'
import SettingTitle from 'components/SettingTitle'
import { OrganisationInformation } from './sections/OrganisationInformation'
import { Force2FASetting } from './sections/admin-settings/Force2FASetting'
import { RestrictProjectCreationSetting } from './sections/admin-settings/RestrictProjectCreationSetting'
import { DeleteOrganisation } from './sections/DeleteOrganisation'

type GeneralTabProps = {
  organisation: Organisation
}

export const GeneralTab = ({ organisation }: GeneralTabProps) => {
  return (
    <div className='col-md-8'>
      <SettingTitle>Organisation Information</SettingTitle>
      <JSONReference title='Organisation' json={organisation} />
      <div className='mt-2'>
        <OrganisationInformation organisation={organisation} />
        <SettingTitle>Admin Settings</SettingTitle>
        <Force2FASetting organisation={organisation} />
        <RestrictProjectCreationSetting organisation={organisation} />
      </div>
      <DeleteOrganisation organisation={organisation} />
    </div>
  )
}
