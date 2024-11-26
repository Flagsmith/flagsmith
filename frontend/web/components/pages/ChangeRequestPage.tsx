import { FC, ReactNode, useEffect, useMemo, useState } from 'react'
import OrganisationStore from 'common/stores/organisation-store'
import ChangeRequestStore from 'common/stores/change-requests-store'
import FeatureListStore from 'common/stores/feature-list-store'
import { useGetMyGroupsQuery } from 'common/services/useMyGroup'
import CreateFlagModal from 'components/modals/CreateFlag'
import AccountStore from 'common/stores/account-store'
import AppActions from 'common/dispatcher/app-actions'
import {
  ChangeRequest,
  Environment,
  FeatureState,
  ProjectChangeRequest,
  ProjectFlag,
  User,
  UserGroupSummary,
} from 'common/types/responses'
import { RouterChildContext } from 'react-router'
import Utils from 'common/utils/utils'
import moment from 'moment'
import ProjectStore from 'common/stores/project-store'
import { useHasPermission } from 'common/providers/Permission'
import { IonIcon } from '@ionic/react'
import { close } from 'ionicons/icons'
import Constants from 'common/constants'
import Button from 'components/base/forms/Button'
import NewVersionWarning from 'components/NewVersionWarning'
import WarningMessage from 'components/WarningMessage'
import Breadcrumb from 'components/Breadcrumb'
import PageTitle from 'components/PageTitle'
import InfoMessage from 'components/InfoMessage'
import InputGroup from 'components/base/forms/InputGroup'
import SettingsButton from 'components/SettingsButton'
import UserSelect from 'components/UserSelect'
import MyGroupsSelect from 'components/MyGroupsSelect'
import Panel from 'components/base/grid/Panel'
import DiffChangeRequest from 'components/diff/DiffChangeRequest'
import JSONReference from 'components/JSONReference'
import ErrorMessage from 'components/ErrorMessage'
import v from 'refractor/lang/v'

type ChangeRequestPageType = {
  router: RouterChildContext['router']
  match: {
    params: {
      environmentId: string
      projectId: string
      id: string
    }
  }
}

const ChangeRequestPage: FC<ChangeRequestPageType> = ({ match, router }) => {
  const { environmentId, id, projectId } = match.params
  const [_, setUpdate] = useState(Date.now())
  const error = ChangeRequestStore.error
  const changeRequest = (
    ChangeRequestStore.model as Record<string, ChangeRequest> | undefined
  )?.[id]
  const flags = (
    ChangeRequestStore.flags as Record<
      string,
      {
        environmentFlag: FeatureState
        projectFlag: ProjectFlag
      }
    >
  )[id]
  const environmentFlag = flags?.environmentFlag
  const projectFlag = flags && flags.projectFlag
  const approvePermission = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission: Utils.getApproveChangeRequestPermission(true),
  })
  const publishPermission = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission: 'UPDATE_FEATURE_STATE',
  })

  useEffect(() => {
    AppActions.getChangeRequest(id, projectId, environmentId)
  }, [id, projectId, environmentId])

  useEffect(() => {
    const forceUpdate = () => {
      setUpdate(Date.now())
    }
    ChangeRequestStore.on('change', forceUpdate)
    FeatureListStore.on('change', forceUpdate)
    OrganisationStore.on('change', forceUpdate)

    return () => {
      ChangeRequestStore.off('change', forceUpdate)
      FeatureListStore.off('change', forceUpdate)
      OrganisationStore.off('change', forceUpdate)
    }
  }, [])

  const addOwner = (id: number, isUser = true) => {
    if (ChangeRequestStore.isLoading || !changeRequest) return
    AppActions.updateChangeRequest({
      approvals: isUser
        ? changeRequest.approvals.concat([{ user: id }])
        : changeRequest.approvals,
      description: changeRequest.description,
      feature_states: changeRequest.feature_states,
      group_assignments: isUser
        ? changeRequest.group_assignments
        : changeRequest.group_assignments.concat([{ group: id }]),
      id: changeRequest.id,
      title: changeRequest.title,
    })
  }

  const removeOwner = (id: number, isUser = true) => {
    if (ChangeRequestStore.isLoading || !changeRequest) return
    AppActions.updateChangeRequest({
      approvals: isUser
        ? changeRequest.approvals.filter((v) => v.user !== id)
        : changeRequest.approvals,
      description: changeRequest.description,
      feature_states: changeRequest.feature_states,
      group_assignments: isUser
        ? changeRequest.group_assignments
        : changeRequest.group_assignments.filter((v) => v.group !== id),
      id: changeRequest.id,
      title: changeRequest.title,
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
        AppActions.deleteChangeRequest(id, () => {
          router.history.replace(
            `/project/${projectId}/environment/${environmentId}/change-requests`,
          )
        })
      },
      title: 'Delete Change Request',
      yesText: 'Confirm',
    })
  }

  const editChangeRequest = (
    projectFlag: ProjectFlag,
    environmentFlag: FeatureState,
  ) => {
    if (!changeRequest) return
    openModal(
      'Edit Change Request',
      <CreateFlagModal
        history={router.history}
        environmentId={environmentId}
        projectId={projectId}
        changeRequest={changeRequest}
        projectFlag={projectFlag}
        multivariate_options={
          changeRequest.feature_states[0].multivariate_feature_state_values
        }
        environmentFlag={{
          ...environmentFlag,
          enabled: changeRequest.feature_states[0].enabled,
          feature_state_value: Utils.featureStateToValue(
            changeRequest.feature_states[0].feature_state_value,
          ),
        }}
        flagId={environmentFlag.id}
      />,
      'side-modal create-feature-modal',
    )
  }

  const approveChangeRequest = () => {
    AppActions.actionChangeRequest(id, 'approve')
  }

  const getScheduledDate = () => {
    if (!changeRequest) return null
    return changeRequest.environment_feature_versions.length > 0
      ? moment(changeRequest.environment_feature_versions[0].live_from)
      : changeRequest?.change_sets?.[0]?.live_from
      ? moment(changeRequest?.change_sets?.[0]?.live_from)
      : moment(changeRequest.feature_states[0].live_from)
  }

  const publishChangeRequest = () => {
    const scheduledDate = getScheduledDate()
    const isScheduled = moment(scheduledDate).valueOf() > moment().valueOf()
    const featureId =
      changeRequest &&
      changeRequest.feature_states[0] &&
      changeRequest.feature_states[0].feature
    const environment = ProjectStore.getEnvironment(
      environmentId,
    ) as unknown as Environment
    openConfirm({
      body: (
        <div>
          Are you sure you want to {isScheduled ? 'schedule' : 'publish'} this
          change request
          {isScheduled
            ? ` for ${moment(scheduledDate).format('Do MMM YYYY hh:mma')}`
            : ''}
          ? This will adjust the feature for your environment.
          <NewVersionWarning
            environmentId={`${environment?.id}`}
            featureId={featureId!}
            date={`${changeRequest?.created_at}`}
          />
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
        AppActions.actionChangeRequest(id, 'commit', () => {
          AppActions.refreshFeatures(projectId, environmentId)
        })
      },
      title: `${isScheduled ? 'Schedule' : 'Publish'} Change Request`,
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
  if (
    !changeRequest ||
    OrganisationStore.isLoading ||
    !projectFlag ||
    !environmentFlag
  ) {
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

  const featureId =
    changeRequest &&
    changeRequest.feature_states[0] &&
    changeRequest.feature_states[0].feature

  const scheduledDate = getScheduledDate()
  const isScheduled = moment(scheduledDate).valueOf() > moment().valueOf()

  const environment = ProjectStore.getEnvironment(
    environmentId,
  ) as unknown as Environment
  const isVersioned = environment?.use_v2_feature_versioning
  const minApprovals = environment.minimum_change_request_approvals || 0

  return (
    <div
      style={{ opacity: ChangeRequestStore.isLoading ? 0.25 : 1 }}
      data-test='change-requests-page'
      id='change-requests-page'
      className='app-container container-fluid mt-1'
    >
      <Breadcrumb
        items={[
          {
            title: isScheduled ? 'Scheduling' : 'Change requests',
            url: `/project/${projectId}/environment/${environmentId}/${
              isScheduled ? 'scheduled-changes' : 'change-requests'
            }`,
          },
        ]}
        currentPage={changeRequest.title}
      />
      <ChangeRequestPageInner
        publishChangeRequest={publishChangeRequest}
        approvePermission={approvePermission?.permission}
        approveChangeRequest={approveChangeRequest}
        publishPermission={publishPermission?.permission}
        isScheduled={isScheduled}
        changeRequest={changeRequest}
        error={error}
        addOwner={addOwner}
        removeOwner={removeOwner}
        publishPermissionDescription={Constants.environmentPermissions(
          'Update Feature States',
        )}
        scheduledDate={getScheduledDate()}
        deleteChangeRequest={deleteChangeRequest}
        editChangeRequest={
          !isVersioned && !changeRequest?.committed_at
            ? () => editChangeRequest(projectFlag, environmentFlag)
            : undefined
        }
        minApprovals={minApprovals || 0}
        DiffView={
          <div>
            <Panel
              title={isScheduled ? 'Scheduled Change' : 'Change Request'}
              className='no-pad mb-2'
            >
              <div className='search-list change-request-list'>
                <Row className='list-item change-request-item px-4'>
                  <div className='font-weight-medium mr-3'>Feature:</div>

                  <a
                    target='_blank'
                    className='btn-link font-weight-medium'
                    href={`/project/${projectId}/environment/${environmentId}/features?feature=${
                      projectFlag && projectFlag.id
                    }`}
                    rel='noreferrer'
                  >
                    {projectFlag?.name}
                  </a>
                </Row>
              </div>
            </Panel>
            <NewVersionWarning
              environmentId={`${environment?.id}`}
              featureId={featureId}
              date={changeRequest.created_at}
            />
            <DiffChangeRequest
              environmentId={environmentId}
              isVersioned={isVersioned}
              changeRequest={changeRequest}
              feature={projectFlag.id}
              projectId={projectId}
            />
          </div>
        }
      />
    </div>
  )
}

type ChangeRequestPageInnerType = {
  deleteChangeRequest: () => void
  minApprovals: number
  addOwner: (id: number, isUser?: boolean) => void
  removeOwner: (id: number, isUser?: boolean) => void
  approveChangeRequest: () => void
  publishPermissionDescription: string
  approvePermission: boolean | undefined
  publishPermission: boolean | undefined
  isScheduled: boolean
  scheduledDate?: moment.Moment | null
  changeRequest: ProjectChangeRequest | ChangeRequest | undefined
  editChangeRequest?: () => void
  publishChangeRequest?: () => void
  DiffView: ReactNode
  error?: any
}

export const ChangeRequestPageInner: FC<ChangeRequestPageInnerType> = ({
  DiffView,
  addOwner,
  approveChangeRequest,
  approvePermission,
  changeRequest,
  deleteChangeRequest,
  editChangeRequest,
  error,
  isScheduled,
  minApprovals,
  publishChangeRequest,
  publishPermission,
  publishPermissionDescription,
  removeOwner,
  scheduledDate,
}) => {
  const organisationId = AccountStore.getOrganisation()?.id
  const { data: myGroups } = useGetMyGroupsQuery(
    {
      orgId: `${organisationId}`,
    },
    {
      skip: !organisationId,
    },
  )
  const groups = useMemo(() => {
    return myGroups?.results
  }, [myGroups])
  const [showUsers, setShowUsers] = useState(false)
  const [showGroups, setShowGroups] = useState(false)

  useEffect(() => {
    if (organisationId) {
      AppActions.getOrganisation(organisationId)
    }
  }, [organisationId])

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
  if (!changeRequest || OrganisationStore.isLoading) {
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

  const getApprovals = (users: User[], approvals: number[]) =>
    users?.filter((v) => approvals?.includes(v.id))

  const getGroupApprovals = (
    groups: UserGroupSummary[],
    approvals: ChangeRequest['group_assignments'],
  ) => groups.filter((v) => approvals.find((a) => a.group === v.id))

  const orgUsers = (OrganisationStore as any).model.users as User[]
  const orgGroups = groups || []
  const ownerUsers =
    changeRequest &&
    getApprovals(
      orgUsers,
      changeRequest.approvals.map((v) => v.user),
    )
  const ownerGroups =
    changeRequest &&
    getGroupApprovals(orgGroups, changeRequest.group_assignments)
  const committedBy =
    changeRequest.committed_by &&
    orgUsers &&
    orgUsers.find((v) => v.id === changeRequest.committed_by)

  const approval =
    changeRequest &&
    changeRequest.approvals.find((v) => v.user === AccountStore.getUser().id)
  const approvedBy = changeRequest.approvals
    .filter((v) => !!v.approved_at)
    .map((v) => {
      const matchingUser = orgUsers.find((u) => u.id === v.user)
      if (!matchingUser) {
        return ''
      }
      return `${matchingUser.first_name} ${matchingUser.last_name}`
    })
  const approved = !!approval && !!approval.approved_at
  const isYourChangeRequest = changeRequest.user === AccountStore.getUser().id

  const user =
    changeRequest &&
    changeRequest.user &&
    orgUsers.find((v) => v.id === changeRequest.user)

  return (
    <div>
      <PageTitle
        cta={
          (!changeRequest.committed_at || isScheduled) && (
            <Row>
              <Button theme='secondary' onClick={deleteChangeRequest}>
                Delete
              </Button>
              {editChangeRequest && (
                <Button onClick={editChangeRequest} className='ml-2'>
                  Edit
                </Button>
              )}
            </Row>
          )
        }
        title={changeRequest.title}
      >
        Created {moment(changeRequest.created_at).format('Do MMM YYYY HH:mma')}{' '}
        by {user ? `${user.first_name} ${user.last_name}` : 'Unknown user'}
      </PageTitle>
      <p className='mt-2'>{changeRequest.description}</p>
      {isScheduled && (
        <div className='col-md-6 mb-4'>
          <InfoMessage icon='calendar' title='Scheduled Change'>
            This feature change will go live at{' '}
            {moment(scheduledDate).format('Do MMM YYYY hh:mma')}
            {changeRequest.committed_at
              ? ' unless it is edited or deleted'
              : ' if it is approved and published'}
            .
            {!!changeRequest.committed_at &&
              'You can still edit / remove the change request before this date.'}
          </InfoMessage>
        </div>
      )}
      <InputGroup
        className='col-md-6'
        component={
          <>
            {!Utils.getFlagsmithHasFeature('disable_users_as_reviewers') && (
              <div className='mb-4'>
                <SettingsButton onClick={() => setShowUsers(true)}>
                  Assigned users
                </SettingsButton>
                <Row className='mt-2'>
                  {ownerUsers.length !== 0 &&
                    ownerUsers.map((u) => (
                      <Row
                        key={u.id}
                        onClick={() => removeOwner(u.id)}
                        className='chip'
                        style={{
                          marginBottom: 4,
                          marginTop: 4,
                        }}
                      >
                        <span className='font-weight-bold'>
                          {u.first_name} {u.last_name}
                        </span>
                        <span className='chip-icon ion'>
                          <IonIcon icon={close} />
                        </span>
                      </Row>
                    ))}
                </Row>
                <UserSelect
                  users={orgUsers}
                  value={ownerUsers && ownerUsers.map((v) => v.id)}
                  onAdd={addOwner}
                  onRemove={removeOwner}
                  isOpen={showUsers}
                  onToggle={() => setShowUsers(!showUsers)}
                />
              </div>
            )}
            <div className='mb-4'>
              <SettingsButton onClick={() => setShowGroups(true)}>
                Assigned groups
              </SettingsButton>
              <Row className='mt-2'>
                {!!ownerGroups?.length &&
                  ownerGroups.map((g) => (
                    <Row
                      key={g.id}
                      onClick={() => removeOwner(g.id, false)}
                      className='chip'
                      style={{
                        marginBottom: 4,
                        marginTop: 4,
                      }}
                    >
                      <span className='font-weight-bold'>{g.name}</span>
                      <span className='chip-icon ion'>
                        <IonIcon icon={close} />
                      </span>
                    </Row>
                  ))}
              </Row>
              <MyGroupsSelect
                orgId={AccountStore.getOrganisation().id}
                value={ownerGroups && ownerGroups.map((v) => v.id)}
                onAdd={addOwner}
                onRemove={removeOwner}
                isOpen={showGroups}
                onToggle={() => setShowGroups(!showGroups)}
              />
            </div>
          </>
        }
      />

      {DiffView}
      <JSONReference
        className='mt-4'
        title={'Change Request'}
        json={changeRequest}
      />
      <Row className='mt-4'>
        <Flex>
          {!!approvedBy?.length && (
            <div className='text-right mb-2 mr-2 font-weight-medium'>
              Feature Approved by {approvedBy.join(', ')}
            </div>
          )}
          {approvedBy.length < minApprovals && (
            <>
              {!!minApprovals && (
                <div className='text-right mb-2 mr-2 font-weight-medium'>
                  You need at least {minApprovals} approval
                  {minApprovals !== 1 ? 's' : ''} to{' '}
                  {isScheduled ? 'schedule' : 'publish'} this change
                </div>
              )}
            </>
          )}
          <ErrorMessage error={error} />
          {changeRequest.committed_at ? (
            <div className='mr-2 font-weight-medium'>
              Committed at{' '}
              {moment(changeRequest.committed_at).format('Do MMM YYYY HH:mma')}{' '}
              {!!committedBy &&
                `
                        by ${committedBy.first_name} ${committedBy.last_name}
                      `}
            </div>
          ) : (
            <Row className='text-right mt-2'>
              <Flex />
              {!isYourChangeRequest &&
                Utils.renderWithPermission(
                  approvePermission,
                  Constants.environmentPermissions('Approve Change Requests'),
                  <Button
                    disabled={approved || !approvePermission}
                    onClick={approveChangeRequest}
                    theme='secondary'
                  >
                    {approved ? 'Approved' : 'Approve'}
                  </Button>,
                )}
              {Utils.renderWithPermission(
                publishPermission,
                publishPermissionDescription,
                <Button
                  disabled={
                    approvedBy.length < minApprovals || !publishPermission
                  }
                  onClick={publishChangeRequest}
                  className='btn ml-2'
                >
                  {isScheduled ? 'Publish Scheduled' : 'Publish'} Change
                </Button>,
              )}
            </Row>
          )}
        </Flex>
      </Row>
    </div>
  )
}

export default ChangeRequestPage
