import React, { FC } from 'react'
import Link from 'components/base/link'

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
        <Link to={orgLink}>Organisation Settings</Link>.
      </span>
    )
  }

  return (
    <span>
      You can create Custom Fields in your{' '}
      <Link to={orgLink}>Organisation Settings</Link> or{' '}
      <Link to={projectLink}>Project Settings</Link>.
    </span>
  )
}

export default RedirectCreateCustomFields
