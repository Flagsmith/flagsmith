import React, { Component } from 'react'
import InviteUsersModal from 'components/modals/InviteUsers'
import UserGroupList from 'components/UserGroupList'
import ConfirmRemoveOrganisation from 'components/modals/ConfirmRemoveOrganisation'
import Payment from 'components/modals/Payment'
import CreateGroupModal from 'components/modals/CreateGroup'
import withAuditWebhooks from 'common/providers/withAuditWebhooks'
import CreateAuditWebhookModal from 'components/modals/CreateAuditWebhook'
import ConfirmRemoveAuditWebhook from 'components/modals/ConfirmRemoveAuditWebhook'
import Button from 'components/base/forms/Button'
import AdminAPIKeys from 'components/AdminAPIKeys'
import Tabs from 'components/base/forms/Tabs'
import TabItem from 'components/base/forms/TabItem'
import InfoMessage from 'components/InfoMessage'
import JSONReference from 'components/JSONReference'
import ConfigProvider from 'common/providers/ConfigProvider'
import OrganisationUsage from 'components/OrganisationUsage'
import Constants from 'common/constants'
import ErrorMessage from 'components/ErrorMessage'
import Format from 'common/utils/format'
import Icon from 'components/Icon'
import OrganisationManageWidget from 'components/OrganisationManageWidget'
import ProjectManageWidget from 'components/ProjectManageWidget'
import { getStore } from 'common/store'
import { getRoles } from 'common/services/useRole'
import _data from 'common/data/base/_data'
import RolesTable from 'components/RolesTable'
import CreateGroup from 'components/modals/CreateGroup'
import PermissionsTabs from 'components/PermissionsTabs'
import UserAction from 'components/UserAction'
import classNames from 'classnames'
import AccountStore from 'common/stores/account-store'

const widths = [300, 200, 80]

const SettingsTab = {
  'Billing': 'billing',
  'General': 'general',
  'Keys': 'keys',
  'Members': 'members',
  'Projects': 'projects',
  'Usage': 'usage',
  'Webhooks': 'webhooks',
}

const OrganisationSettingsPage = class extends Component {
  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  static displayName = 'OrganisationSettingsPage'

  constructor(props, context) {
    super(props, context)
    this.state = {
      manageSubscriptionLoaded: true,
      permissions: [],
      role: 'ADMIN',
      roles: [],
    }
    if (!AccountStore.getOrganisation()) {
      return
    }
    AppActions.getOrganisation(AccountStore.getOrganisation().id)
    this.props.getWebhooks()

    this.getOrganisationPermissions(AccountStore.getOrganisation().id)
  }

  componentDidMount = () => {
    if (!AccountStore.getOrganisation()) {
      return
    }
    getRoles(
      getStore(),
      { organisation_id: AccountStore.getOrganisation().id },
      { forceRefetch: true },
    ).then((roles) => {
      this.setState({ roles: roles.data.results })
    })
    API.trackPage(Constants.pages.ORGANISATION_SETTINGS)
    $('body').trigger('click')
    if (
      AccountStore.getUser() &&
      AccountStore.getOrganisationRole() !== 'ADMIN'
    ) {
      this.setState({ permissionsError: true })
    }
  }

  onSave = () => {
    this.setState({ name: null }, () => {
      toast('Saved organisation')
    })
  }

  onChange = () => {
    this.props.getWebhooks()
  }

  confirmRemove = (organisation, cb) => {
    openModal(
      'Delete Organisation',
      <ConfirmRemoveOrganisation organisation={organisation} cb={cb} />,
      'p-0',
    )
  }

  onRemove = () => {
    toast('Your organisation has been removed')
    if (AccountStore.getOrganisation()) {
      this.context.router.history.replace('/organisation-settings')
    } else {
      this.context.router.history.replace('/create')
    }
  }

  deleteInvite = (id) => {
    openConfirm({
      body: (
        <div>
          Are you sure you want to delete this invite? This action cannot be
          undone.
        </div>
      ),
      destructive: true,
      onYes: () => AppActions.deleteInvite(id),
      title: 'Delete Invite',
      yesText: 'Confirm',
    })
  }

  deleteUser = (id, userDisplayName) => {
    openConfirm({
      body: (
        <div>
          Are you sure you want to remove the user{' '}
          <strong>{userDisplayName}</strong> from the organisation? This action
          cannot be undone.
        </div>
      ),
      destructive: true,
      onYes: () => AppActions.deleteUser(id),
      title: 'Delete User',
      yesText: 'Confirm',
    })
  }

  save = (e) => {
    e && e.preventDefault()
    const {
      force_2fa,
      name,
      restrict_project_create_to_admin,
      webhook_notification_email,
    } = this.state
    if (AccountStore.isSaving) {
      return
    }

    const org = AccountStore.getOrganisation()
    AppActions.editOrganisation({
      force_2fa,
      name: name || org.name,
      restrict_project_create_to_admin:
        typeof restrict_project_create_to_admin === 'boolean'
          ? restrict_project_create_to_admin
          : undefined,
      webhook_notification_email:
        webhook_notification_email !== undefined
          ? webhook_notification_email
          : org.webhook_notification_email,
    })
  }

  save2FA = (force_2fa) => {
    const {
      name,
      restrict_project_create_to_admin,
      webhook_notification_email,
    } = this.state
    if (AccountStore.isSaving) {
      return
    }

    const org = AccountStore.getOrganisation()
    AppActions.editOrganisation({
      force_2fa,
      name: name || org.name,
      restrict_project_create_to_admin:
        typeof restrict_project_create_to_admin === 'boolean'
          ? restrict_project_create_to_admin
          : undefined,
      webhook_notification_email:
        webhook_notification_email !== undefined
          ? webhook_notification_email
          : org.webhook_notification_email,
    })
  }

  setAdminCanCreateProject = (restrict_project_create_to_admin) => {
    this.setState({ restrict_project_create_to_admin }, this.save)
  }

  saveDisabled = () => {
    const { name, webhook_notification_email } = this.state
    if (
      AccountStore.isSaving ||
      (!name && webhook_notification_email === undefined)
    ) {
      return true
    }

    // Must have name
    if (name !== undefined && !name) {
      return true
    }

    // Must be valid email for webhook notification email
    return (
      webhook_notification_email &&
      !Utils.isValidEmail(webhook_notification_email)
    )
  }

  roleChanged = (id, { value: role }) => {
    AppActions.updateUserRole(id, role)
  }

  createWebhook = () => {
    openModal(
      'New Webhook',
      <CreateAuditWebhookModal
        router={this.context.router}
        save={this.props.createWebhook}
      />,
      'side-modal',
    )
  }

  editWebhook = (webhook) => {
    openModal(
      'Edit Webhook',
      <CreateAuditWebhookModal
        router={this.context.router}
        webhook={webhook}
        isEdit
        save={this.props.saveWebhook}
      />,
      'side-modal',
    )
  }

  editGroup = (group) => {
    openModal(
      'Edit Group',
      <CreateGroup
        roles={this.state.roles}
        isEdit
        orgId={AccountStore.getOrganisation().id}
        group={group}
      />,
      'side-modal',
    )
  }

  deleteWebhook = (webhook) => {
    openModal(
      'Remove Webhook',
      <ConfirmRemoveAuditWebhook
        url={webhook.url}
        cb={() => this.props.deleteWebhook(webhook)}
      />,
      'p-0',
    )
  }

  editUserPermissions = (user, organisationId) => {
    openModal(
      'Edit Organisation Permissions',
      <div className='p-4'>
        <PermissionsTabs uncontrolled user={user} orgId={organisationId} />
      </div>,
      'p-0 side-modal',
    )
  }
  formatLastLoggedIn = (last_login) => {
    if (!last_login) return 'Never'

    const diff = moment().diff(moment(last_login), 'days')
    if (diff >= 30) {
      return (
        <div className='mb-1'>
          {`${diff} days ago`}
          <br />
          <div className='list-item-subtitle'>
            {moment(last_login).format('Do MMM YYYY')}
          </div>
        </div>
      )
    }
    return 'Within 30 days'
  }

  getOrganisationPermissions = (id) => {
    if (this.state.permissions.length) return

    const url = `${Project.api}organisations/${id}/my-permissions/`
    _data.get(url).then(({ permissions }) => {
      this.setState({ permissions })
    })
  }

  render() {
    const {
      props: { webhooks, webhooksLoading },
    } = this
    const hasRbacPermission = Utils.getPlansPermission('RBAC')
    const paymentsEnabled = Utils.getFlagsmithHasFeature('payments_enabled')
    const force2faPermission = Utils.getPlansPermission('FORCE_2FA')
    const verifySeatsLimit = Utils.getFlagsmithHasFeature(
      'verify_seats_limit_for_invite_links',
    )

    return (
      <div className='app-container container'>
        <AccountProvider
          onSave={this.onSave}
          onRemove={this.onRemove}
          onChange={this.onChange}
        >
          {({ isSaving, organisation }, { deleteOrganisation }) =>
            !!organisation && (
              <OrganisationProvider id={AccountStore.getOrganisation()?.id}>
                {({
                  error,
                  invalidateInviteLink,
                  inviteLinks,
                  invites,
                  isLoading,
                  name,
                  subscriptionMeta,
                  users,
                }) => {
                  const { max_seats } = subscriptionMeta ||
                    organisation.subscription || { max_seats: 1 }
                  const isAWS =
                    AccountStore.getPaymentMethod() === 'AWS_MARKETPLACE'
                  const { chargebee_email } = subscriptionMeta || {}
                  const autoSeats =
                    !isAWS && Utils.getPlansPermission('AUTO_SEATS')
                  const usedSeats =
                    paymentsEnabled && organisation.num_seats >= max_seats
                  const overSeats =
                    paymentsEnabled && organisation.num_seats > max_seats
                  const needsUpgradeForAdditionalSeats =
                    (overSeats && (!verifySeatsLimit || !autoSeats)) ||
                    (!autoSeats && usedSeats)
                  const displayedTabs = [SettingsTab.Projects]

                  if (this.state.permissionsError) {
                    displayedTabs.push(
                      ...[SettingsTab.Members].filter((v) => !!v),
                    )
                  } else {
                    displayedTabs.push(
                      ...[
                        SettingsTab.General,
                        paymentsEnabled && !isAWS ? SettingsTab.Billing : null,
                        SettingsTab.Keys,
                        SettingsTab.Members,
                        SettingsTab.Webhooks,
                      ].filter((v) => !!v),
                    )

                    if (!Project.disableAnalytics) {
                      displayedTabs.push(SettingsTab.Usage)
                    }
                  }
                  return (
                    <div>
                      <div className='py-4'>
                        <OrganisationManageWidget />
                      </div>

                      <Tabs hideNavOnSingleTab urlParam='tab' className='mt-0'>
                        {displayedTabs.includes(SettingsTab.Projects) && (
                          <TabItem tabLabel='Projects'>
                            <h5 className='mt-4 mb-2'>Projects</h5>

                            <p className='fs-small lh-sm mb-4'>
                              Projects let you create and manage a set of
                              features and configure them between multiple app
                              environments.
                            </p>

                            <ProjectManageWidget
                              organisationId={organisation.id}
                            />
                          </TabItem>
                        )}

                        {displayedTabs.includes(SettingsTab.General) && (
                          <TabItem tabLabel='General'>
                            <FormGroup className='mt-4'>
                              <h5 className='mb-5'>General Settings</h5>
                              <JSONReference
                                title={'Organisation'}
                                json={organisation}
                              />
                              <div className='mt-2'>
                                <div className='col-md-8'>
                                  <form
                                    key={organisation.id}
                                    onSubmit={this.save}
                                  >
                                    <Row>
                                      <Flex>
                                        <InputGroup
                                          ref={(e) => (this.input = e)}
                                          data-test='organisation-name'
                                          value={
                                            this.state.name || organisation.name
                                          }
                                          onChange={(e) =>
                                            this.setState({
                                              name: Utils.safeParseEventValue(
                                                e,
                                              ),
                                            })
                                          }
                                          isValid={name && name.length}
                                          type='text'
                                          inputClassName='input--wide'
                                          placeholder='My Organisation'
                                          title='Organisation Name'
                                          inputProps={{
                                            className: 'full-width',
                                          }}
                                        />
                                      </Flex>
                                      <Button
                                        type='submit'
                                        disabled={this.saveDisabled()}
                                        className='ml-3'
                                      >
                                        {isSaving ? 'Updating' : 'Update Name'}
                                      </Button>
                                    </Row>
                                  </form>
                                </div>
                                <hr className='mt-0 mb-4' />
                                {Utils.getFlagsmithHasFeature('force_2fa') && (
                                  <div className='col-md-6'>
                                    <Row className='mt-4 mb-2'>
                                      {!force2faPermission ? (
                                        <Tooltip
                                          title={
                                            <Switch
                                              checked={organisation.force_2fa}
                                              onChange={this.save2FA}
                                            />
                                          }
                                        >
                                          To access this feature please upgrade
                                          your account to scaleup or higher."
                                        </Tooltip>
                                      ) : (
                                        <Switch
                                          checked={organisation.force_2fa}
                                          onChange={this.save2FA}
                                        />
                                      )}
                                      <h5 className='mb-0 ml-3'>Enforce 2FA</h5>
                                    </Row>
                                    <p className='fs-small lh-sm'>
                                      Enabling this setting forces users within
                                      the organisation to setup 2 factor
                                      security.
                                    </p>
                                  </div>
                                )}
                                {Utils.getFlagsmithHasFeature(
                                  'restrict_project_create_to_admin',
                                ) && (
                                  <FormGroup className='mt-4 col-md-6'>
                                    <h5>Admin Settings</h5>
                                    <Row className='mb-2'>
                                      <Switch
                                        checked={
                                          organisation.restrict_project_create_to_admin
                                        }
                                        onChange={() =>
                                          this.setAdminCanCreateProject(
                                            !organisation.restrict_project_create_to_admin,
                                          )
                                        }
                                      />
                                      <p className='fs-small ml-3 mb-0 lh-sm'>
                                        Only allow organisation admins to create
                                        projects
                                      </p>
                                    </Row>
                                  </FormGroup>
                                )}
                              </div>
                            </FormGroup>
                            <hr className='my-4' />
                            <FormGroup className='mt-4 col-md-6'>
                              <Row space>
                                <div className='col-md-7'>
                                  <h5 className='mn-2'>Delete Organisation</h5>
                                  <p className='fs-small lh-sm'>
                                    This organisation will be permanently
                                    deleted, along with all projects and
                                    features.
                                  </p>
                                </div>
                                <Button
                                  id='delete-org-btn'
                                  onClick={() =>
                                    this.confirmRemove(organisation, () => {
                                      deleteOrganisation()
                                    })
                                  }
                                  className='btn-with-icon btn-remove'
                                >
                                  <Icon
                                    name='trash-2'
                                    width={20}
                                    fill='#EF4D56'
                                  />
                                </Button>
                              </Row>
                            </FormGroup>
                          </TabItem>
                        )}
                        {displayedTabs.includes(SettingsTab.Billing) && (
                          <TabItem tabLabel='Billing'>
                            <div className='mt-4'>
                              <Row space className='plan p-4 mb-4'>
                                <div>
                                  <Row>
                                    <div>
                                      <Row
                                        className='mr-3'
                                        style={{ width: '230px' }}
                                      >
                                        <div className='plan-icon'>
                                          <Icon name='layers' width={32} />
                                        </div>
                                        <div>
                                          <p className='fs-small lh-sm mb-0'>
                                            Your plan
                                          </p>
                                          <h4 className='mb-0'>
                                            {Utils.getPlanName(
                                              _.get(
                                                organisation,
                                                'subscription.plan',
                                              ),
                                            )
                                              ? Utils.getPlanName(
                                                  _.get(
                                                    organisation,
                                                    'subscription.plan',
                                                  ),
                                                )
                                              : 'Free'}
                                          </h4>
                                        </div>
                                      </Row>
                                    </div>
                                    <div>
                                      <Row
                                        style={{ width: '230px' }}
                                        className='mr-3'
                                      >
                                        <div className='plan-icon'>
                                          <h4
                                            className='mb-0 text-center'
                                            style={{ width: '32px' }}
                                          >
                                            ID
                                          </h4>
                                        </div>
                                        <div>
                                          <p className='fs-small lh-sm mb-0'>
                                            Organisation ID
                                          </p>
                                          <h4 className='mb-0'>
                                            {organisation.id}
                                          </h4>
                                        </div>
                                      </Row>
                                    </div>
                                    {!!chargebee_email && (
                                      <div>
                                        <Row style={{ width: '230px' }}>
                                          <div className='plan-icon'>
                                            <Icon name='layers' width={32} />
                                          </div>
                                          <div>
                                            <p className='fs-small lh-sm mb-0'>
                                              Management Email
                                            </p>
                                            <h6 className='mb-0'>
                                              {chargebee_email}
                                            </h6>
                                          </div>
                                        </Row>
                                      </div>
                                    )}
                                  </Row>
                                </div>
                                <div className='align-self-start'>
                                  {organisation.subscription
                                    ?.subscription_id && (
                                    <Button
                                      theme='secondary'
                                      href='https://flagsmith.chargebeeportal.com/'
                                      target='_blank'
                                      className='btn'
                                    >
                                      Manage Invoices
                                    </Button>
                                  )}
                                </div>
                              </Row>
                              <Payment viewOnly={false} />
                            </div>
                          </TabItem>
                        )}

                        {displayedTabs.includes(SettingsTab.Keys) && (
                          <TabItem tabLabel='API Keys'>
                            <AdminAPIKeys organisationId={organisation.id} />
                          </TabItem>
                        )}

                        {displayedTabs.includes(SettingsTab.Members) && (
                          <TabItem
                            data-test='tab-permissions'
                            tabLabel='Members'
                          >
                            <JSONReference
                              showNamesButton
                              className='mt-4'
                              title={'Members'}
                              json={users}
                            />
                            <JSONReference
                              title={'Invite Links'}
                              json={inviteLinks}
                            />

                            <FormGroup className='mt-4'>
                              <div className='col-md-8'>
                                <h5 className='mb-2'>
                                  Manage Users and Permissions
                                </h5>
                                <p className='mb-4 fs-small lh-sm'>
                                  Flagsmith lets you manage fine-grained
                                  permissions for your projects and
                                  environments, invite members as a user or an
                                  administrator and then set permission in your
                                  Project and Environment settings.{' '}
                                  <Button
                                    theme='text'
                                    href='https://docs.flagsmith.com/system-administration/rbac'
                                    target='_blank'
                                    className='fw-normal'
                                  >
                                    Learn about User Roles.
                                  </Button>
                                </p>
                              </div>
                              <div>
                                <div>
                                  <div>
                                    {isLoading && (
                                      <div className='centered-container'>
                                        <Loader />
                                      </div>
                                    )}
                                    {!isLoading && (
                                      <div>
                                        <Tabs
                                          urlParam={'type'}
                                          theme='pill'
                                          uncontrolled
                                        >
                                          <TabItem tabLabel='Members'>
                                            <Row space className='mt-4'>
                                              <h5 className='mb-0'>
                                                Team Members
                                              </h5>
                                              {Utils.renderWithPermission(
                                                !this.state.permissionsError,
                                                Constants.organisationPermissions(
                                                  'Admin',
                                                ),
                                                <Button
                                                  disabled={
                                                    needsUpgradeForAdditionalSeats ||
                                                    this.state.permissionsError
                                                  }
                                                  id='btn-invite'
                                                  onClick={() =>
                                                    openModal(
                                                      'Invite Users',
                                                      <InviteUsersModal />,
                                                      'p-0 side-modal',
                                                    )
                                                  }
                                                  type='button'
                                                  size='small'
                                                >
                                                  Invite members
                                                </Button>,
                                              )}
                                            </Row>
                                            <FormGroup className='mt-2'>
                                              {paymentsEnabled &&
                                                !isLoading && (
                                                  <div className='col-md-6 mt-3 mb-4'>
                                                    <InfoMessage>
                                                      {
                                                        'You are currently using '
                                                      }
                                                      <strong
                                                        className={
                                                          overSeats
                                                            ? 'text-danger'
                                                            : ''
                                                        }
                                                      >
                                                        {`${organisation.num_seats} of ${max_seats}`}
                                                      </strong>
                                                      {` seat${
                                                        organisation.num_seats ===
                                                        1
                                                          ? ''
                                                          : 's'
                                                      } `}{' '}
                                                      for your plan.{' '}
                                                      {usedSeats && (
                                                        <>
                                                          {overSeats &&
                                                          (!verifySeatsLimit ||
                                                            !autoSeats) ? (
                                                            <strong>
                                                              If you wish to
                                                              invite any
                                                              additional
                                                              members, please{' '}
                                                              {
                                                                <a
                                                                  href='#'
                                                                  onClick={
                                                                    Utils.openChat
                                                                  }
                                                                >
                                                                  Contact us
                                                                </a>
                                                              }
                                                              .
                                                            </strong>
                                                          ) : needsUpgradeForAdditionalSeats ? (
                                                            <strong>
                                                              If you wish to
                                                              invite any
                                                              additional
                                                              members, please{' '}
                                                              {
                                                                <a
                                                                  href='#'
                                                                  onClick={() => {
                                                                    this.props.router.history.replace(
                                                                      `${
                                                                        document
                                                                          .location
                                                                          .pathname
                                                                      }?${Utils.toParam(
                                                                        {
                                                                          ...Utils.fromParam(),
                                                                          tab: this
                                                                            .state
                                                                            .tab
                                                                            ? 'closed'
                                                                            : 'open',
                                                                        },
                                                                      )}`,
                                                                    )
                                                                  }}
                                                                >
                                                                  Upgrade your
                                                                  plan
                                                                </a>
                                                              }
                                                              .
                                                            </strong>
                                                          ) : (
                                                            <strong>
                                                              You will
                                                              automatically be
                                                              charged $20/month
                                                              for each
                                                              additional member
                                                              that joins your
                                                              organisation.
                                                            </strong>
                                                          )}
                                                        </>
                                                      )}
                                                    </InfoMessage>
                                                  </div>
                                                )}
                                              {inviteLinks &&
                                                (!verifySeatsLimit ||
                                                  !needsUpgradeForAdditionalSeats) && (
                                                  <form
                                                    onSubmit={(e) => {
                                                      e.preventDefault()
                                                    }}
                                                  >
                                                    <div className='mt-3'>
                                                      <Row>
                                                        <div
                                                          className='mr-3'
                                                          style={{ width: 257 }}
                                                        >
                                                          <Select
                                                            value={{
                                                              label:
                                                                this.state
                                                                  .role ===
                                                                'ADMIN'
                                                                  ? 'Organisation Administrator'
                                                                  : 'User',
                                                              value:
                                                                this.state.role,
                                                            }}
                                                            onChange={(v) =>
                                                              this.setState({
                                                                role: v.value,
                                                              })
                                                            }
                                                            options={[
                                                              {
                                                                label:
                                                                  'Organisation Administrator',
                                                                value: 'ADMIN',
                                                              },
                                                              {
                                                                isDisabled:
                                                                  !hasRbacPermission,
                                                                label:
                                                                  hasRbacPermission
                                                                    ? 'User'
                                                                    : 'User - Please upgrade for role based access',
                                                                value: 'USER',
                                                              },
                                                            ]}
                                                            className='react-select select-sm'
                                                          />
                                                        </div>
                                                        {inviteLinks.find(
                                                          (f) =>
                                                            f.role ===
                                                            this.state.role,
                                                        ) && (
                                                          <>
                                                            <Flex className='mr-4'>
                                                              <Input
                                                                style={{
                                                                  width: 257,
                                                                }}
                                                                value={`${
                                                                  document
                                                                    .location
                                                                    .origin
                                                                }/invite-link/${
                                                                  inviteLinks.find(
                                                                    (f) =>
                                                                      f.role ===
                                                                      this.state
                                                                        .role,
                                                                  ).hash
                                                                }`}
                                                                data-test='invite-link'
                                                                inputClassName='input input--wide'
                                                                type='text'
                                                                readonly='readonly'
                                                                title={
                                                                  <h3>Link</h3>
                                                                }
                                                                placeholder='Link'
                                                                size='small'
                                                              />
                                                            </Flex>
                                                            <Row>
                                                              <Button
                                                                theme='secondary'
                                                                size='small'
                                                                onClick={() => {
                                                                  navigator.clipboard.writeText(
                                                                    `${
                                                                      document
                                                                        .location
                                                                        .origin
                                                                    }/invite/${
                                                                      inviteLinks.find(
                                                                        (f) =>
                                                                          f.role ===
                                                                          this
                                                                            .state
                                                                            .role,
                                                                      ).hash
                                                                    }`,
                                                                  )
                                                                  toast(
                                                                    'Link copied',
                                                                  )
                                                                }}
                                                              >
                                                                Copy Invite Link
                                                              </Button>
                                                              <Button
                                                                className='ml-3'
                                                                size='small'
                                                                type='button'
                                                                onClick={() => {
                                                                  openConfirm({
                                                                    body: 'This will generate a new invite link for the selected role, users will no longer be able to use the existing one. Are you sure?',
                                                                    onYes:
                                                                      () => {
                                                                        invalidateInviteLink(
                                                                          inviteLinks.find(
                                                                            (
                                                                              f,
                                                                            ) =>
                                                                              f.role ===
                                                                              this
                                                                                .state
                                                                                .role,
                                                                          ),
                                                                        )
                                                                      },
                                                                    title:
                                                                      'Regenerate Invite Link',
                                                                    yesText:
                                                                      'Confirm',
                                                                  })
                                                                }}
                                                              >
                                                                Regenerate
                                                              </Button>
                                                            </Row>
                                                          </>
                                                        )}
                                                      </Row>
                                                    </div>
                                                    <p className='my-4 col-md-8'>
                                                      Anyone with link can join
                                                      as a standard user, once
                                                      they have joined you can
                                                      edit their role from the
                                                      team members panel.{' '}
                                                      <Button
                                                        theme='text'
                                                        target='_blank'
                                                        href='https://docs.flagsmith.com/advanced-use/permissions'
                                                        className='fw-normal'
                                                      >
                                                        Learn about User Roles.
                                                      </Button>
                                                    </p>
                                                    <div className='text-right mt-2'>
                                                      {error && (
                                                        <ErrorMessage
                                                          error={error}
                                                        />
                                                      )}
                                                    </div>
                                                  </form>
                                                )}
                                              <PanelSearch
                                                id='org-members-list'
                                                title='Members'
                                                className='no-pad'
                                                header={
                                                  <Row className='table-header'>
                                                    <Flex className='table-column px-3'>
                                                      User
                                                    </Flex>
                                                    <div
                                                      className='table-column'
                                                      style={{
                                                        minWidth: widths[0],
                                                      }}
                                                    >
                                                      Role
                                                    </div>
                                                    <div
                                                      style={{
                                                        width: widths[1],
                                                      }}
                                                      className='table-column'
                                                    >
                                                      Last logged in
                                                    </div>
                                                    <div
                                                      style={{
                                                        width: widths[2],
                                                      }}
                                                      className='table-column text-center'
                                                    >
                                                      Actions
                                                    </div>
                                                  </Row>
                                                }
                                                items={users}
                                                itemHeight={65}
                                                renderRow={(user, i) => {
                                                  const {
                                                    email,
                                                    first_name,
                                                    id,
                                                    last_login,
                                                    last_name,
                                                    role,
                                                  } = user

                                                  const onRemoveClick = () => {
                                                    this.deleteUser(
                                                      id,
                                                      Format.userDisplayName({
                                                        email,
                                                        firstName: first_name,
                                                        lastName: last_name,
                                                      }),
                                                      email,
                                                    )
                                                  }
                                                  const onEditClick = () => {
                                                    if (role !== 'ADMIN') {
                                                      this.editUserPermissions(
                                                        user,
                                                        organisation.id,
                                                      )
                                                    }
                                                  }
                                                  return (
                                                    <Row
                                                      data-test={`user-${i}`}
                                                      space
                                                      className={classNames(
                                                        'list-item',
                                                        {
                                                          clickable:
                                                            role !== 'ADMIN',
                                                        },
                                                      )}
                                                      onClick={onEditClick}
                                                      key={id}
                                                    >
                                                      <Flex className='table-column px-3 font-weight-medium'>
                                                        {`${first_name} ${last_name}`}{' '}
                                                        {id ===
                                                          AccountStore.getUserId() &&
                                                          '(You)'}
                                                        <div className='list-item-subtitle mt-1'>
                                                          {email}
                                                        </div>
                                                      </Flex>

                                                      <div
                                                        style={{
                                                          width: widths[0],
                                                        }}
                                                        className='table-column'
                                                      >
                                                        <div>
                                                          {organisation.role ===
                                                            'ADMIN' &&
                                                          id !==
                                                            AccountStore.getUserId() ? (
                                                            <div>
                                                              <Select
                                                                data-test='select-role'
                                                                placeholder='Select a role'
                                                                value={
                                                                  role && {
                                                                    label:
                                                                      Constants
                                                                        .roles[
                                                                        role
                                                                      ],
                                                                    value: role,
                                                                  }
                                                                }
                                                                onChange={(e) =>
                                                                  this.roleChanged(
                                                                    id,
                                                                    Utils.safeParseEventValue(
                                                                      e,
                                                                    ),
                                                                  )
                                                                }
                                                                options={_.map(
                                                                  Constants.roles,
                                                                  (
                                                                    label,
                                                                    value,
                                                                  ) => ({
                                                                    isDisabled:
                                                                      value !==
                                                                        'ADMIN' &&
                                                                      !hasRbacPermission,
                                                                    label:
                                                                      value !==
                                                                        'ADMIN' &&
                                                                      !hasRbacPermission
                                                                        ? `${label} - Please upgrade for role based access`
                                                                        : label,
                                                                    value,
                                                                  }),
                                                                )}
                                                                menuPortalTarget={
                                                                  document.body
                                                                }
                                                                menuPosition='absolute'
                                                                menuPlacement='auto'
                                                                className='react-select select-xsm'
                                                              />
                                                            </div>
                                                          ) : (
                                                            <div className='px-3 fs-small lh-sm'>
                                                              {Constants.roles[
                                                                role
                                                              ] || ''}
                                                            </div>
                                                          )}
                                                        </div>
                                                      </div>
                                                      <div
                                                        style={{
                                                          width: widths[1],
                                                        }}
                                                        className='table-column'
                                                      >
                                                        <div className='fs-small lh-sm'>
                                                          {this.formatLastLoggedIn(
                                                            last_login,
                                                          )}
                                                        </div>
                                                      </div>
                                                      <div
                                                        style={{
                                                          width: widths[2],
                                                        }}
                                                        className='table-column text-end'
                                                      >
                                                        <UserAction
                                                          onRemove={
                                                            onRemoveClick
                                                          }
                                                          onEdit={onEditClick}
                                                          canRemove={AccountStore.isAdmin()}
                                                          canEdit={
                                                            role !== 'ADMIN'
                                                          }
                                                        />
                                                      </div>
                                                    </Row>
                                                  )
                                                }}
                                                renderNoResults={
                                                  <div>
                                                    You have no users in this
                                                    organisation.
                                                  </div>
                                                }
                                                filterRow={(item, search) => {
                                                  const strToSearch = `${item.first_name} ${item.last_name} ${item.email}`
                                                  return (
                                                    strToSearch
                                                      .toLowerCase()
                                                      .indexOf(
                                                        search.toLowerCase(),
                                                      ) !== -1
                                                  )
                                                }}
                                              />
                                              <div id='select-portal' />
                                            </FormGroup>

                                            {invites && invites.length ? (
                                              <FormGroup className='margin-top'>
                                                <PanelSearch
                                                  itemHeight={70}
                                                  id='org-invites-list'
                                                  title='Invites Pending'
                                                  className='no-pad'
                                                  items={_.sortBy(
                                                    invites,
                                                    'email',
                                                  )}
                                                  header={
                                                    <Row className='table-header'>
                                                      <Flex className='table-column px-3'>
                                                        User
                                                      </Flex>
                                                      <div
                                                        style={{
                                                          width: widths[0],
                                                        }}
                                                        className='table-column'
                                                      >
                                                        Role
                                                      </div>
                                                      <div
                                                        style={{
                                                          width: widths[1],
                                                        }}
                                                        className='table-column'
                                                      >
                                                        Action
                                                      </div>
                                                    </Row>
                                                  }
                                                  renderRow={(
                                                    {
                                                      date_created,
                                                      email,
                                                      id,
                                                      invited_by,
                                                      link,
                                                    },
                                                    i,
                                                  ) => (
                                                    <Row
                                                      data-test={`pending-invite-${i}`}
                                                      className='list-item'
                                                      key={id}
                                                    >
                                                      <div className='flex flex-1 px-3'>
                                                        {email || link}
                                                        <div className='list-item-subtitle mt-1'>
                                                          Created{' '}
                                                          {moment(
                                                            date_created,
                                                          ).format(
                                                            'DD/MMM/YYYY',
                                                          )}
                                                        </div>
                                                        {invited_by ? (
                                                          <div className='list-item-subtitle'>
                                                            Invited by{' '}
                                                            {invited_by.first_name
                                                              ? `${invited_by.first_name} ${invited_by.last_name}`
                                                              : invited_by.email}
                                                          </div>
                                                        ) : null}
                                                      </div>
                                                      <div
                                                        style={{
                                                          width: widths[0],
                                                        }}
                                                        className='table-column'
                                                      >
                                                        {link ? (
                                                          ' '
                                                        ) : (
                                                          <Button
                                                            id='resend-invite'
                                                            type='button'
                                                            onClick={() =>
                                                              AppActions.resendInvite(
                                                                id,
                                                              )
                                                            }
                                                            theme='text'
                                                            size='small'
                                                          >
                                                            Resend
                                                          </Button>
                                                        )}
                                                      </div>
                                                      <div
                                                        className='table-column text-center'
                                                        style={{
                                                          width: widths[5],
                                                        }}
                                                      >
                                                        <Button
                                                          id='delete-invite'
                                                          type='button'
                                                          onClick={() =>
                                                            this.deleteInvite(
                                                              id,
                                                            )
                                                          }
                                                          className='btn btn-with-icon'
                                                        >
                                                          <Icon
                                                            name='trash-2'
                                                            width={20}
                                                            fill='#656D7B'
                                                          />
                                                        </Button>
                                                      </div>
                                                    </Row>
                                                  )}
                                                  filterRow={(item, search) =>
                                                    item.email
                                                      .toLowerCase()
                                                      .indexOf(
                                                        search.toLowerCase(),
                                                      ) !== -1
                                                  }
                                                />
                                              </FormGroup>
                                            ) : null}
                                          </TabItem>
                                          <TabItem tabLabel='Groups'>
                                            <div>
                                              <Row space className='mt-4 mb-1'>
                                                <h5 className='mb-0'>
                                                  User Groups
                                                </h5>
                                                {Utils.renderWithPermission(
                                                  !this.state.permissionsError,
                                                  Constants.organisationPermissions(
                                                    'Admin',
                                                  ),
                                                  <Button
                                                    id='btn-invite'
                                                    disabled={
                                                      this.state
                                                        .permissionsError
                                                    }
                                                    onClick={() =>
                                                      openModal(
                                                        'Create Group',
                                                        <CreateGroupModal
                                                          orgId={
                                                            organisation.id
                                                          }
                                                        />,
                                                        'side-modal',
                                                      )
                                                    }
                                                    type='button'
                                                    size='small'
                                                  >
                                                    Create Group
                                                  </Button>,
                                                )}
                                              </Row>
                                              <p className='col-md-8 mb-4'>
                                                Groups allow you to manage
                                                permissions for viewing and
                                                editing projects, features and
                                                environments.
                                              </p>
                                              <UserGroupList
                                                showRemove
                                                onClick={this.editGroup}
                                                orgId={organisation.id}
                                              />
                                            </div>
                                          </TabItem>
                                          {Utils.getFlagsmithHasFeature(
                                            'show_role_management',
                                          ) && (
                                            <TabItem tabLabel='Roles'>
                                              {hasRbacPermission ? (
                                                <>
                                                  <RolesTable
                                                    organisationId={
                                                      organisation.id
                                                    }
                                                    users={users}
                                                  />
                                                </>
                                              ) : (
                                                <div className='mt-4'>
                                                  <InfoMessage>
                                                    To use <strong>role</strong>{' '}
                                                    features you have to upgrade
                                                    your plan.
                                                  </InfoMessage>
                                                </div>
                                              )}
                                            </TabItem>
                                          )}
                                        </Tabs>
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            </FormGroup>
                          </TabItem>
                        )}

                        {displayedTabs.includes(SettingsTab.Webhooks) && (
                          <TabItem tabLabel='Webhooks'>
                            <FormGroup className='mt-4'>
                              <JSONReference
                                title={'Webhooks'}
                                json={webhooks}
                              />

                              <Column className='mb-3 ml-0 col-md-8'>
                                <h5 className='mb-2'>Audit Webhooks</h5>
                                <p className='fs-small lh-sm mb-4'>
                                  Audit webhooks let you know when audit logs
                                  occur, you can configure 1 or more audit
                                  webhooks per organisation.{' '}
                                  <Button
                                    theme='text'
                                    href='https://docs.flagsmith.com/system-administration/webhooks'
                                    className='fw-normal'
                                  >
                                    Learn about Audit Webhooks.
                                  </Button>
                                </p>
                                <Button onClick={this.createWebhook}>
                                  Create audit webhook
                                </Button>
                              </Column>
                              {webhooksLoading && !webhooks ? (
                                <Loader />
                              ) : (
                                <PanelSearch
                                  id='webhook-list'
                                  title={
                                    <Tooltip
                                      title={
                                        <h5 className='mb-0'>
                                          Webhooks <Icon name='info' />
                                        </h5>
                                      }
                                      place='right'
                                    >
                                      {Constants.strings.WEBHOOKS_DESCRIPTION}
                                    </Tooltip>
                                  }
                                  items={webhooks}
                                  renderRow={(webhook) => (
                                    <Row
                                      onClick={() => {
                                        this.editWebhook(webhook)
                                      }}
                                      space
                                      className='list-item clickable cursor-pointer'
                                      key={webhook.id}
                                    >
                                      <Flex className='table-column px-3'>
                                        <div className='font-weight-medium mb-1'>
                                          {webhook.url}
                                        </div>
                                        {webhook.created_at ? (
                                          <div className='list-item-description'>
                                            Created{' '}
                                            {moment(webhook.created_at).format(
                                              'DD/MMM/YYYY',
                                            )}
                                          </div>
                                        ) : null}
                                      </Flex>
                                      <div className='table-column'>
                                        <Switch checked={webhook.enabled} />
                                      </div>
                                      <div className='table-column'>
                                        <Button
                                          id='delete-invite'
                                          type='button'
                                          onClick={(e) => {
                                            e.stopPropagation()
                                            e.preventDefault()
                                            this.deleteWebhook(webhook)
                                          }}
                                          className='btn btn-with-icon'
                                        >
                                          <Icon
                                            name='trash-2'
                                            width={20}
                                            fill='#656D7B'
                                          />
                                        </Button>
                                      </div>
                                    </Row>
                                  )}
                                  renderNoResults={
                                    <Panel
                                      className='no-pad'
                                      title={
                                        <Tooltip
                                          title={
                                            <h5 className='mb-0'>
                                              Webhooks{' '}
                                              <Icon name='info-outlined' />
                                            </h5>
                                          }
                                          place='right'
                                        >
                                          {
                                            Constants.strings
                                              .AUDIT_WEBHOOKS_DESCRIPTION
                                          }
                                        </Tooltip>
                                      }
                                    >
                                      <div className='search-list'>
                                        <Row className='list-item p-3 text-muted'>
                                          You currently have no webhooks
                                          configured for this organisation.
                                        </Row>
                                      </div>
                                    </Panel>
                                  }
                                  isLoading={this.props.webhookLoading}
                                />
                              )}
                            </FormGroup>
                          </TabItem>
                        )}

                        {displayedTabs.includes(SettingsTab.Usage) && (
                          <TabItem tabLabel='Usage'>
                            {Utils.fromParam().tab === 'usage' && (
                              <OrganisationUsage
                                organisationId={organisation.id}
                              />
                            )}
                          </TabItem>
                        )}
                      </Tabs>
                    </div>
                  )
                }}
              </OrganisationProvider>
            )
          }
        </AccountProvider>
      </div>
    )
  }
}

OrganisationSettingsPage.propTypes = {}

module.exports = ConfigProvider(withAuditWebhooks(OrganisationSettingsPage))
