import WarningMessage from 'components/WarningMessage'
import React from 'react'
import { ProjectSettingsTabProps } from 'components/pages/project-settings/shared/types'

export const CustomFieldsTab = ({
  organisationId,
}: ProjectSettingsTabProps) => (
  <div className='mt-4'>
    <h5>Custom Fields</h5>

    <WarningMessage
      warningMessage={
        <span>
          Custom fields have been moved to{' '}
          <a
            href={`/organisation/${organisationId}/settings?tab=custom-fields`}
            rel='noreferrer'
          >
            Organisation Settings
          </a>
          .
        </span>
      }
    />
  </div>
)
