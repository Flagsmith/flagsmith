import React, { Component } from 'react'
import ChangeRequestStore from 'common/stores/change-requests-store'
import OrganisationStore from 'common/stores/organisation-store'
import FeatureListStore from 'common/stores/feature-list-store'
import withSegmentOverrides from 'common/providers/withSegmentOverrides'
import ProjectStore from 'common/stores/project-store'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
import Button from 'components/base/forms/Button'
import UserSelect from 'components/UserSelect'
import CreateFlagModal from 'components/modals/CreateFlag'
import InfoMessage from 'components/InfoMessage'
import Permission from 'common/providers/Permission'
import JSONReference from 'components/JSONReference'
import MyGroupsSelect from 'components/MyGroupsSelect'
import { getMyGroups } from 'common/services/useMyGroup'
import { getStore } from 'common/store'
import PageTitle from 'components/PageTitle'
import { close } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'
import Breadcrumb from 'components/Breadcrumb'
import SettingsButton from 'components/SettingsButton'
import DiffChangeRequest from 'components/diff/DiffChangeRequest'

const ChangeRequestsPage = class extends Component {
  static displayName = 'ChangeRequestsPage'

  static contextTypes = {
    router: propTypes.object.isRequired,
  }
  getApprovals = (users, approvals) =>
    users?.filter((v) => approvals?.includes(v.id))

  getGroupApprovals = (groups, approvals) =>
    groups.filter((v) => approvals.find((a) => a.group === v.id))

  constructor(props, context) {
    super(props, context)
    this.state = {
      showArchived: false,
      tags: [],
    }
    ES6Component(this)
    this.listenTo(ChangeRequestStore, 'change', () => this.forceUpdate())
    this.listenTo(FeatureListStore, 'change', () => this.forceUpdate())
    this.listenTo(OrganisationStore, 'change', () => this.forceUpdate())
    this.listenTo(ChangeRequestStore, 'problem', () =>
      this.setState({ error: true }),
    )
    AppActions.getChangeRequest(
      this.props.match.params.id,
      this.props.match.params.projectId,
      this.props.match.params.environmentId,
    )
    AppActions.getOrganisation(AccountStore.getOrganisation().id)
    getMyGroups(getStore(), { orgId: AccountStore.getOrganisation().id }).then(
      (res) => {
        this.setState({ groups: res?.data?.results || [] })
      },
    )
  }

  removeOwner = (id, isUser = true) => {
    if (ChangeRequestStore.isLoading) return
    const changeRequest = ChangeRequestStore.model[this.props.match.params.id]
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

  addOwner = (id, isUser = true) => {
    if (ChangeRequestStore.isLoading) return
    const changeRequest = ChangeRequestStore.model[this.props.match.params.id]
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
  componentDidMount = () => {}

  deleteChangeRequest = () => {
    openConfirm({
      body: (
        <div>
          Are you sure you want to delete this change request? This action
          cannot be undone.
        </div>
      ),
      destructive: true,
      onYes: () => {
        AppActions.deleteChangeRequest(this.props.match.params.id, () => {
          this.context.router.history.replace(
            `/project/${this.props.match.params.projectId}/environment/${this.props.match.params.environmentId}/change-requests`,
          )
        })
      },
      title: 'Delete Change Request',
      yesText: 'Confirm',
    })
  }

  editChangeRequest = (projectFlag, environmentFlag) => {
    const id = this.props.match.params.id
    const changeRequest = ChangeRequestStore.model[id]

    openModal(
      'Edit Change Request',
      <CreateFlagModal
        history={this.props.router.history}
        environmentId={this.props.match.params.environmentId}
        projectId={this.props.match.params.projectId}
        changeRequest={ChangeRequestStore.model[id]}
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

  approveChangeRequest = () => {
    AppActions.actionChangeRequest(this.props.match.params.id, 'approve')
  }

  publishChangeRequest = () => {
    const id = this.props.match.params.id
    const changeRequest = ChangeRequestStore.model[id]
    const isScheduled =
      new Date(changeRequest.feature_states[0].live_from).valueOf() >
      new Date().valueOf()
    const scheduledDate = moment(changeRequest.feature_states[0].live_from)

    openConfirm({
      body: (
        <div>
          Are you sure you want to {isScheduled ? 'schedule' : 'publish'} this
          change request
          {isScheduled
            ? ` for ${scheduledDate.format('Do MMM YYYY hh:mma')}`
            : ''}
          ? This will adjust the feature for your environment.
        </div>
      ),
      onYes: () => {
        AppActions.actionChangeRequest(
          this.props.match.params.id,
          'commit',
          () => {
            AppActions.refreshFeatures(
              this.props.match.params.projectId,
              this.props.match.params.environmentId,
              true,
            )
          },
        )
      },
      title: `${isScheduled ? 'Schedule' : 'Publish'} Change Request`,
    })
  }

  fetchFeature = (featureId) => {
    this.activeFeature = featureId
  }

  render() {
    const id = this.props.match.params.id
    const changeRequest = ChangeRequestStore.model[id]
    const flags = ChangeRequestStore.flags[id]
    const environmentFlag = flags && flags.environmentFlag
    const projectFlag = flags && flags.projectFlag

    if (this.state.error && !changeRequest) {
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
    const orgUsers = OrganisationStore.model && OrganisationStore.model.users
    const orgGroups = this.state.groups || []
    const ownerUsers =
      changeRequest &&
      this.getApprovals(
        orgUsers,
        changeRequest.approvals.map((v) => v.user),
      )
    const ownerGroups =
      changeRequest &&
      this.getGroupApprovals(orgGroups, changeRequest.group_assignments)
    const featureId =
      changeRequest &&
      changeRequest.feature_states[0] &&
      changeRequest.feature_states[0].feature
    if (featureId !== this.activeFeature) {
      this.fetchFeature(featureId)
    }
    const user =
      changeRequest &&
      changeRequest.user &&
      orgUsers.find((v) => v.id === changeRequest.user)
    const committedBy =
      (changeRequest.committed_by &&
        orgUsers &&
        orgUsers.find((v) => v.id === changeRequest.committed_by)) ||
      {}
    const isScheduled =
      new Date(changeRequest.feature_states[0].live_from).valueOf() >
      new Date().valueOf()

    const scheduledDate = moment(changeRequest.feature_states[0].live_from)

    const approval =
      changeRequest &&
      changeRequest.approvals.find((v) => v.user === AccountStore.getUser().id)
    const approvedBy = changeRequest.approvals
      .filter((v) => !!v.approved_at)
      .map((v) => {
        const matchingUser = orgUsers.find((u) => u.id === v.user) || {}
        return `${matchingUser.first_name} ${matchingUser.last_name}`
      })
    const approved = !!approval && !!approval.approved_at
    const environment = ProjectStore.getEnvironment(
      this.props.match.params.environmentId,
    )
    const isVersioned = environment?.use_v2_feature_versioning
    const minApprovals = environment.minimum_change_request_approvals || 0
    const isYourChangeRequest = changeRequest.user === AccountStore.getUser().id

    return (
      <Permission
        level='environment'
        permission={Utils.getApproveChangeRequestPermission(true)}
        id={this.props.match.params.environmentId}
      >
        {({ permission: approvePermission }) => (
          <Permission
            level='environment'
            permission='UPDATE_FEATURE_STATE'
            id={this.props.match.params.environmentId}
          >
            {({ permission: publishPermission }) => (
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
                      url: `/project/${
                        this.props.match.params.projectId
                      }/environment/${this.props.match.params.environmentId}/${
                        isScheduled ? 'scheduled-changes' : 'change-requests'
                      }`,
                    },
                  ]}
                  currentPage={changeRequest.title}
                />
                <PageTitle
                  cta={
                    (!changeRequest?.committed_at ||
                      moment(changeRequest?.feature_states[0].live_from) >
                        moment()) && (
                      <Row>
                        <Button
                          theme='secondary'
                          onClick={this.deleteChangeRequest}
                        >
                          Delete
                        </Button>
                        {!isVersioned && (
                          <Button
                            onClick={() =>
                              this.editChangeRequest(
                                projectFlag,
                                environmentFlag,
                              )
                            }
                            className='ml-2'
                          >
                            Edit
                          </Button>
                        )}
                      </Row>
                    )
                  }
                  title={changeRequest.title}
                >
                  Created{' '}
                  {moment(changeRequest.created_at).format(
                    'Do MMM YYYY HH:mma',
                  )}{' '}
                  by{' '}
                  {user
                    ? `${user.first_name} ${user.last_name}`
                    : 'Unknown user'}
                </PageTitle>
                <p className='mt-2'>{changeRequest.description}</p>
                {isScheduled && (
                  <div className='col-md-6 mb-4'>
                    <InfoMessage icon='calendar' title='Scheduled Change'>
                      This feature change{' '}
                      {changeRequest?.committedAt ? 'is scheduled to' : 'will'}{' '}
                      go live at {scheduledDate.format('Do MMM YYYY hh:mma')}
                      {changeRequest?.committed_at
                        ? ' unless it is edited or deleted'
                        : ' if it is approved and published'}
                      .
                      {!!changeRequest?.committedAt &&
                        'You can still edit / remove the change request before this date.'}
                    </InfoMessage>
                  </div>
                )}
                <InputGroup
                  className='col-md-6'
                  component={
                    <>
                      {!Utils.getFlagsmithHasFeature(
                        'disable_users_as_reviewers',
                      ) && (
                        <div className='mb-4'>
                          <SettingsButton
                            onClick={() => this.setState({ showUsers: true })}
                          >
                            Assigned users
                          </SettingsButton>
                          <Row className='mt-2'>
                            {ownerUsers.length !== 0 &&
                              ownerUsers.map((u) => (
                                <Row
                                  key={u.id}
                                  onClick={() => this.removeOwner(u.id)}
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
                            onAdd={this.addOwner}
                            onRemove={this.removeOwner}
                            isOpen={this.state.showUsers}
                            onToggle={() =>
                              this.setState({
                                showUsers: !this.state.showUsers,
                              })
                            }
                          />
                        </div>
                      )}
                      <div className='mb-4'>
                        <SettingsButton
                          onClick={() => this.setState({ showGroups: true })}
                        >
                          Assigned groups
                        </SettingsButton>
                        <Row className='mt-2'>
                          {!!ownerGroups?.length &&
                            ownerGroups.map((g) => (
                              <Row
                                key={g.id}
                                onClick={() => this.removeOwner(g.id, false)}
                                className='chip'
                                style={{
                                  marginBottom: 4,
                                  marginTop: 4,
                                }}
                              >
                                <span className='font-weight-bold'>
                                  {g.name}
                                </span>
                                <span className='chip-icon ion'>
                                  <IonIcon icon={close} />
                                </span>
                              </Row>
                            ))}
                        </Row>
                        <MyGroupsSelect
                          orgId={AccountStore.getOrganisation().id}
                          groups={orgGroups}
                          value={ownerGroups && ownerGroups.map((v) => v.id)}
                          onAdd={this.addOwner}
                          onRemove={this.removeOwner}
                          isOpen={this.state.showGroups}
                          onToggle={() =>
                            this.setState({
                              showGroups: !this.state.showGroups,
                            })
                          }
                        />
                      </div>
                    </>
                  }
                />

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
                          href={`/project/${
                            this.props.match.params.projectId
                          }/environment/${
                            this.props.match.params.environmentId
                          }/features?feature=${projectFlag && projectFlag.id}`}
                          rel='noreferrer'
                        >
                          {projectFlag && projectFlag.name}
                        </a>
                      </Row>
                    </div>
                  </Panel>
                  <DiffChangeRequest
                    isVersioned={isVersioned}
                    changeRequest={changeRequest}
                    feature={projectFlag.id}
                    projectId={this.props.match.params.projectId}
                  />
                </div>
                <JSONReference
                  className='mt-4'
                  title={'Change Request'}
                  json={ChangeRequestStore.model?.[id]}
                />
                <Row className='mt-4'>
                  <Flex>
                    {approvedBy.length ? (
                      <div className='text-right mb-2 mr-2 font-weight-medium'>
                        Approved by {approvedBy.join(', ')}
                      </div>
                    ) : (
                      !!minApprovals && (
                        <div className='text-right mb-2 mr-2 font-weight-medium'>
                          You need at least {minApprovals} approval
                          {minApprovals !== 1 ? 's' : ''} to{' '}
                          {isScheduled ? 'schedule' : 'publish'} this change
                        </div>
                      )
                    )}

                    {changeRequest.committed_at ? (
                      <div className='mr-2 font-weight-medium'>
                        Committed at{' '}
                        {moment(changeRequest.committed_at).format(
                          'Do MMM YYYY HH:mma',
                        )}{' '}
                        by {committedBy.first_name} {committedBy.last_name}
                      </div>
                    ) : (
                      <Row className='text-right mt-2'>
                        <Flex />
                        {!isYourChangeRequest &&
                          Utils.renderWithPermission(
                            approvePermission,
                            Constants.environmentPermissions(
                              'Approve Change Requests',
                            ),
                            <Button
                              disabled={approved || !approvePermission}
                              onClick={this.approveChangeRequest}
                              theme='secondary'
                            >
                              {approved ? 'Approved' : 'Approve'}
                            </Button>,
                          )}
                        {Utils.renderWithPermission(
                          publishPermission,
                          Constants.environmentPermissions(
                            'Update Feature States',
                          ),
                          <Button
                            disabled={
                              approvedBy.length < minApprovals ||
                              !publishPermission
                            }
                            onClick={this.publishChangeRequest}
                            className='btn ml-2'
                          >
                            {isScheduled ? 'Publish Scheduled' : 'Publish'}{' '}
                            Change
                          </Button>,
                        )}
                      </Row>
                    )}
                  </Flex>
                </Row>
              </div>
            )}
          </Permission>
        )}
      </Permission>
    )
  }
}

ChangeRequestsPage.propTypes = {}

module.exports = ConfigProvider(withSegmentOverrides(ChangeRequestsPage))
