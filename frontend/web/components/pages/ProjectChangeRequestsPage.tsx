import { FC, useEffect, useState } from 'react'
import { RouterChildContext } from 'react-router'
import AccountStore from 'common/stores/account-store'
import AppActions from 'common/dispatcher/app-actions'
import Utils from 'common/utils/utils'
import { Link } from 'react-router-dom'
import InfoMessage from 'components/InfoMessage'
import { ChangeRequestsInner } from './ChangeRequestsPage'
import { useGetProjectChangeRequestsQuery } from 'common/services/useProjectChangeRequest'
import { useGetProjectQuery } from 'common/services/useProject'

type ProjectChangeRequestsPageType = {
  router: RouterChildContext['router']
  match: {
    params: {
      environmentId: string
      projectId: string
    }
  }
}

const ProjectChangeRequestsPage: FC<ProjectChangeRequestsPageType> = ({
  match,
  router,
}) => {
  const { environmentId, projectId } = match.params
  const [page, setPage] = useState(1)
  const [pageCommitted, setPageCommitted] = useState(1)
  const organisationId = AccountStore.getOrganisation()?.id
  const { data: project } = useGetProjectQuery({ id: projectId })
  // @ts-ignore

  const { data: committed, isLoading: committedLoading } =
    useGetProjectChangeRequestsQuery({
      committed: true,
      page: pageCommitted,
      page_size: 10,
      project_id: projectId,
    })

  const { data: changeRequests, isLoading } = useGetProjectChangeRequestsQuery({
    committed: false,
    page,
    page_size: 10,
    project_id: projectId,
  })

  useEffect(() => {
    AppActions.getOrganisation(organisationId)
  }, [organisationId])

  return (
    <ChangeRequestsInner
      feature={'4_EYES_PROJECT'}
      committedChangeRequests={committed}
      pageCommitted={pageCommitted}
      isLoading={isLoading}
      setPageCommitted={setPageCommitted}
      page={page}
      getLink={(id) => `/project/${projectId}/change-requests/${id}`}
      setPage={setPage}
      changeRequests={changeRequests}
      changeRequestsDisabled={
        !Utils.changeRequestsEnabled(project?.minimum_change_request_approvals)
      }
      ChangeRequestsDisabledMessage={
        <InfoMessage>
          To enable this feature set a minimum number of approvals in{' '}
          <Link
            to={`/project/${projectId}/environment/${environmentId}/settings`}
          >
            Environment Settings
          </Link>
        </InfoMessage>
      }
    />
  )
}

export default ProjectChangeRequestsPage
