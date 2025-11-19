import InfoMessage from 'components/InfoMessage'
import WarningMessage from 'components/WarningMessage'
import React from 'react'

type CustomFieldsTabProps = {
  organisationId: number
}

export const CustomFieldsTab = ({ organisationId }: CustomFieldsTabProps) => {
  // Runtime safety check
  if (!organisationId) {
    return (
      <div className='mt-4'>
        <InfoMessage>Unable to load organisation settings</InfoMessage>
      </div>
    )
  }

  return (
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
}
