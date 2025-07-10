import React, { FC } from 'react'
import Icon from './Icon'
import { useGetProjectChangeRequestsQuery } from 'common/services/useProjectChangeRequest'
import Utils from 'common/utils/utils'
import { useGetProjectQuery } from 'common/services/useProject'
import NavSubLink from './navigation/NavSubLink'

type ProjectChangeRequestsLinkType = {
  projectId: string
}

const ProjectChangeRequestsLink: FC<ProjectChangeRequestsLinkType> = ({
  projectId,
}) => {
  const { data: project } = useGetProjectQuery(
    { id: projectId },
    { skip: !projectId },
  )
  const { data: changeRequestsData } = useGetProjectChangeRequestsQuery(
    {
      committed: false,
      page_size: 1,
      project_id: projectId,
    },
    { skip: !projectId },
  )
  const changeRequests =
    Utils.changeRequestsEnabled(project?.minimum_change_request_approvals) &&
    changeRequestsData?.count
  if (!Utils.getFlagsmithHasFeature('segment_change_requests')) {
    return null
  }
  return (
    <NavSubLink
      icon={<Icon name='request' />}
      id={`segments-link`}
      to={`/project/${projectId}/change-requests`}
    >
      Change Requests{' '}
      {changeRequests ? (
        <span className='ms-1 unread d-inline'>{changeRequests}</span>
      ) : null}
    </NavSubLink>
  )
}

export default ProjectChangeRequestsLink
