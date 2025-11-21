import React from 'react'
import JSONReference from 'components/JSONReference'
import SettingTitle from 'components/SettingTitle'
import { Project } from 'common/types/responses'
import { ProjectInformation } from './sections/ProjectInformation'
import { AdditionalSettings } from './sections/additional-settings'
import { EdgeAPIMigration } from './sections/EdgeAPIMigration'
import { DeleteProject } from './sections/DeleteProject'

type GeneralTabProps = {
  project: Project
  environmentId?: string
}

export const GeneralTab = ({ project }: GeneralTabProps) => {
  return (
    <div className='mt-4 col-md-8'>
      <JSONReference title='Project' json={project} className='mb-3' />

      <SettingTitle>Project Information</SettingTitle>
      <label>Project Name</label>

      <ProjectInformation project={project} />

      <SettingTitle>Additional Settings</SettingTitle>

      <AdditionalSettings project={project} />

      <EdgeAPIMigration project={project} />

      <DeleteProject project={project} />
    </div>
  )
}
