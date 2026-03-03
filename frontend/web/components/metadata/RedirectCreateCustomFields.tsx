import React, { FC } from 'react'

type RedirectCreateCustomFieldsProps = {
  organisationId: number
  projectId?: number
  organisationOnly: boolean
}

const RedirectCreateCustomFields: FC<RedirectCreateCustomFieldsProps> = ({
  organisationId,
  organisationOnly,
  projectId,
}) => {
  const orgLink = `/organisation/${organisationId}/settings?tab=custom-fields`
  const projectLink = `/project/${projectId}/settings?tab=custom-fields`

  if (organisationOnly) {
    return (
      <span>
        You can create Organisation Custom Fields in your{' '}
        <a href={orgLink} rel='noreferrer'>
          Organisation Settings
        </a>
        .
      </span>
    )
  }

  return (
    <span>
      You can create Custom Fields in your{' '}
      <a href={orgLink} rel='noreferrer'>
        Organisation Settings
      </a>{' '}
      or{' '}
      <a href={projectLink} rel='noreferrer'>
        Project Settings
      </a>
      .
    </span>
  )
}

export default RedirectCreateCustomFields
