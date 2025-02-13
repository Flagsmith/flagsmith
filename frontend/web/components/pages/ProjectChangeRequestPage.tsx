import { FC } from 'react'
import OrganisationStore from 'common/stores/organisation-store'
import ChangeRequestStore from 'common/stores/change-requests-store'
import { Environment } from 'common/types/responses'
import { RouterChildContext } from 'react-router'
import Utils from 'common/utils/utils'
import ProjectStore from 'common/stores/project-store'
import { useHasPermission } from 'common/providers/Permission'
import Constants from 'common/constants'
import WarningMessage from 'components/WarningMessage'
import Breadcrumb from 'components/Breadcrumb'
import Panel from 'components/base/grid/Panel'
import {
  useActionProjectChangeRequestMutation,
  useDeleteProjectChangeRequestMutation,
  useGetProjectChangeRequestQuery,
  useUpdateProjectChangeRequestMutation,
} from 'common/services/useProjectChangeRequest'
import { ChangeRequestPageInner } from './ChangeRequestPage'
import { useGetSegmentQuery } from 'common/services/useSegment'
import { useGetProjectQuery } from 'common/services/useProject'
import DiffSegment from 'components/diff/DiffSegment'
import ConfigProvider from "common/providers/ConfigProvider";

type ProjectChangeRequestPageType = {
  router: RouterChildContext['router']
  match: {
    params: {
      projectId: string
      id: string
    }
  }
}

const ProjectChangeRequestPage: FC<ProjectChangeRequestPageType> = ({
  match,
  router,
}) => {
  const { id, projectId } = match.params
  const error = ChangeRequestStore.error
  const approvePermission = useHasPermission({
    id: projectId,
    level: 'project',
    permission: 'MANAGE_SEGMENTS',
  })
  const publishPermission = useHasPermission({
    id: projectId,
    level: 'project',
    permission: 'MANAGE_SEGMENTS',
  })
  const { data: project } = useGetProjectQuery({ id: projectId })
  const [actionChangeRequest, { isLoading: isActioning }] =
    useActionProjectChangeRequestMutation({})
  const [deleteProjectChangeRequest, { isLoading: isDeleting }] =
    useDeleteProjectChangeRequestMutation({})
  const { data: changeRequest, isLoading: changeRequestLoading } =
    useGetProjectChangeRequestQuery(
      {
        id,
        project_id: projectId,
      },
      { skip: !projectId || !id },
    )
  const [updateChangeRequest, { isLoading: isUpdating }] =
    useUpdateProjectChangeRequestMutation({})
  const segmentId = changeRequest?.segments?.[0]?.version_of
  const { data: segment } = useGetSegmentQuery(
    {
      id: `${segmentId}`,
      projectId,
    },
    {
      skip: !segmentId,
    },
  )

  const addOwner = (id: number, isUser = true) => {
    if (isUpdating || !changeRequest) return
    updateChangeRequest({
      data: {
        ...changeRequest,
        approvals: isUser
          ? changeRequest.approvals.concat([{ user: id }])
          : changeRequest.approvals,
        group_assignments: isUser
          ? changeRequest.group_assignments
          : changeRequest.group_assignments.concat([{ group: id }]),
      },
      project_id: projectId,
    })
  }

  const removeOwner = (id: number, isUser = true) => {
    if (ChangeRequestStore.isLoading || !changeRequest) return
    updateChangeRequest({
      data: {
        ...changeRequest,
        approvals: isUser
          ? changeRequest.approvals.filter((v) => v.user !== id)
          : changeRequest.approvals,
        group_assignments: isUser
          ? changeRequest.group_assignments
          : changeRequest.group_assignments.filter((v) => v.group !== id),
      },
      project_id: projectId,
    })
  }

  const deleteChangeRequest = () => {
    openConfirm({
      body: (
        <div>
          Are you sure you want to delete this change request? This action
          cannot be undone.
        </div>
      ),
      destructive: true,
      onYes: () => {
        deleteProjectChangeRequest({
          id: `${changeRequest!.id}`,
          project_id: projectId,
        }).then((res) => {
          // @ts-ignore
          if (!res.error) {
            router.history.replace(`/project/${projectId}/change-requests`)
            toast('Deleted change request')
          } else {
            toast('Could not delete change request', 'danger')
          }
        })
      },
      title: 'Delete Change Request',
      yesText: 'Confirm',
    })
  }

  const approveChangeRequest = () => {
    actionChangeRequest({
      actionType: 'approve',
      id: `${changeRequest!.id}`,
      project_id: projectId,
    })
  }

  const publishChangeRequest = () => {
    openConfirm({
      body: (
        <div>
          Are you sure you want to publish this change request ? This will
          adjust the segment for your project.
          {!!changeRequest?.conflicts?.length && (
            <div className='mt-2'>
              <WarningMessage
                warningMessage={
                  <div>
                    A change request was published since the creation of this
                    one that also modified this feature. Please review the
                    changes on this page to make sure they are correct.
                  </div>
                }
              />
            </div>
          )}
        </div>
      ),
      onYes: () => {
        actionChangeRequest({
          actionType: 'commit',
          id: `${changeRequest!.id}`,
          project_id: projectId,
        })
      },
      title: `Publish Change Request`,
    })
  }

  if (error && !changeRequest) {
    return (
      <div
        data-test='change-requests-page'
        id='change-requests-page'
        className='app-container container'
      >
        <h3>Change Request not Found</h3>
        <p>The Change Request may have been deleted.</p>
      </div>
    )
  }
  if (!changeRequest || OrganisationStore.isLoading || !segment || !project) {
    return (
      <div
        data-test='change-requests-page'
        id='change-requests-page'
        className='app-container container'
      >
        <div className='text-center'>
          <Loader />
        </div>
      </div>
    )
  }

  const minApprovals = project.minimum_change_request_approvals || 0
  const isLoading =
    changeRequestLoading || isActioning || isDeleting || isUpdating
  return (
    <div
      style={{ opacity: isLoading ? 0.25 : 1 }}
      data-test='change-requests-page'
      id='change-requests-page'
      className='app-container container-fluid mt-1'
    >
      <Breadcrumb
        items={[
          {
            title: 'Change requests',
            url: `/project/${projectId}/change-requests`,
          },
        ]}
        currentPage={changeRequest.title}
      />
      <ChangeRequestPageInner
        isScheduled={false}
        publishChangeRequest={publishChangeRequest}
        approvePermission={approvePermission?.permission}
        approveChangeRequest={approveChangeRequest}
        publishPermission={publishPermission?.permission}
        changeRequest={changeRequest}
        error={error}
        addOwner={addOwner}
        removeOwner={removeOwner}
        publishPermissionDescription={Constants.environmentPermissions(
          'Update Feature States',
        )}
        deleteChangeRequest={deleteChangeRequest}
        minApprovals={minApprovals || 0}
        DiffView={
          <div>
            <Panel title={'Change Request'} className='no-pad mb-2'>
              <div className='search-list change-request-list'>
                <Row className='list-item change-request-item px-4'>
                  <div className='font-weight-medium mr-3'>Segment:</div>
                  <a
                    target='_blank'
                    className='btn-link font-weight-medium'
                    href={`/project/4236/segments?featureSpecific=${!segment.feature}&id=${
                      segment.id
                    }`}
                    rel='noreferrer'
                  >
                    {segment?.name}
                  </a>
                </Row>
              </div>
            </Panel>
            <DiffSegment
              oldSegment={segment}
              newSegment={changeRequest.segments[0]}
            />
            {/*<DiffChangeRequest*/}
            {/*  environmentId={environmentId}*/}
            {/*  isVersioned={isVersioned}*/}
            {/*  changeRequest={changeRequest}*/}
            {/*  feature={projectFlag.id}*/}
            {/*  projectId={projectId}*/}
            {/*/>*/}
          </div>
        }
      />
    </div>
  )
}

export default ConfigProvider(ProjectChangeRequestPage)
