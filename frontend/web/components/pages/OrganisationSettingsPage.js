import React, { Component } from 'react'
import InviteUsersModal from 'components/modals/InviteUsers'
import UserGroupList from 'components/UserGroupList'
import ConfirmRemoveOrganisation from 'components/modals/ConfirmRemoveOrganisation'
import PaymentModal from 'components/modals/Payment'
import CreateGroupModal from 'components/modals/CreateGroup'
import withAuditWebhooks from 'common/providers/withAuditWebhooks'
import CreateAuditWebhookModal from 'components/modals/CreateAuditWebhook'
import ConfirmRemoveAuditWebhook from 'components/modals/ConfirmRemoveAuditWebhook'
import ConfirmDeleteRole from 'components/modals/ConfirmDeleteRole'
import Button from 'components/base/forms/Button'
import { EditPermissionsModal } from 'components/EditPermissions'
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
import CreateRole from 'components/modals/CreateRole'
import Icon from 'components/Icon'
import PageTitle from 'components/PageTitle'

const widths = [450, 150, 100]
const rolesWidths = [250, 600, 100]
const OrganisationSettingsPage = class extends Component {
  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  static displayName = 'OrganisationSettingsPage'

  constructor(props, context) {
    super(props, context)
    this.state = {
      manageSubscriptionLoaded: true,
      role: 'ADMIN',
    }
    if (!AccountStore.getOrganisation()) {
      return
    }
    AppActions.getOrganisation(AccountStore.getOrganisation().id)
    this.props.getWebhooks()
  }

  componentDidMount = () => {
    AppActions.getRoles(AccountStore.getOrganisation().id)
    API.trackPage(Constants.pages.ORGANISATION_SETTINGS)
    $('body').trigger('click')
    if (
      AccountStore.getUser() &&
      AccountStore.getOrganisationRole() !== 'ADMIN'
    ) {
      this.context.router.history.replace('/projects')
    }
  }

  onSave = () => {
    toast('Saved organisation')
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
      this.context.router.history.replace('/projects')
    } else {
      this.context.router.history.replace('/create')
    }
  }

  deleteInvite = (id) => {
    openConfirm(
      'Delete Invite',
      <div>Are you sure you want to delete this invite?</div>,
      () => AppActions.deleteInvite(id),
    )
  }

  deleteUser = (id, userDisplayName) => {
    openConfirm(
      'Remove User',
      <div>
        Are you sure you want to remove the user{' '}
        <strong>{userDisplayName}</strong> from the organisation?
      </div>,
      () => AppActions.deleteUser(id),
    )
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

  editUserPermissions = (user) => {
    openModal(
      'Edit Organisation Permissions',
      <EditPermissionsModal
        name={`${user.first_name} ${user.last_name}`}
        id={AccountStore.getOrganisation().id}
        onSave={() => {
          AppActions.getOrganisation(AccountStore.getOrganisation().id)
        }}
        level='organisation'
        user={user}
      />,
      'p-0 side-modal',
    )
  }

  editGroupPermissions = (group) => {
    openModal(
      'Edit Organisation Permissions',
      <EditPermissionsModal
        name={`${group.name}`}
        id={AccountStore.getOrganisation().id}
        isGroup
        onSave={() => {
          AppActions.getOrganisation(AccountStore.getOrganisation().id)
        }}
        level='organisation'
        group={group}
        push={this.context.router.history.push}
      />,
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

  createRole = (organisationId) => {
    openModal(
      'Create Role',
      <CreateRole
        organisationId={organisationId}
        onComplete={() => {
          AppActions.getRoles(organisationId)
          toast('Role created')
          closeModal()
        }}
      />,
      'side-modal',
    )
  }
  deleteRole = (role) => {
    openModal(
      'Remove Role',
      <ConfirmDeleteRole
        role={role}
        onComplete={() => {
          AppActions.getRoles(role.organisation)
          toast('Role Deleted')
        }}
      />,
      'p-0',
    )
  }
  editRole = (role) => {
    openModal(
      'Edit Role and Permissions',
      <CreateRole
        isEdit
        role={role}
        onComplete={() => {
          AppActions.getRoles(role.organisation)
          toast('Role updated')
        }}
      />,
      'side-modal',
    )
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
        <PageTitle title='Manage' />
        <AccountProvider onSave={this.onSave} onRemove={this.onRemove}>
          {({ isSaving, organisation }, { deleteOrganisation }) =>
            !!organisation && (
              <OrganisationProvider>
                {({
                  error,
                  invalidateInviteLink,
                  inviteLinks,
                  invites,
                  isLoading,
                  name,
                  roles,
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
                  return (
                    <div>
                      <Tabs
                        value={this.state.tab || 0}
                        onChange={(tab) => this.setState({ tab })}
                        className='mt-0'
                      >
                        <TabItem tabLabel='General'>
                          <FormGroup className='mt-4'>
                            <div className='mt-4'>
                              <div>
                                <JSONReference
                                  title={'Organisation'}
                                  json={organisation}
                                />
                                <form
                                  key={organisation.id}
                                  onSubmit={this.save}
                                >
                                  <h5>Organisation Name</h5>
                                  <Row>
                                    <Column className='ml-0'>
                                      <Input
                                        ref={(e) => (this.input = e)}
                                        data-test='organisation-name'
                                        value={
                                          this.state.name || organisation.name
                                        }
                                        onChange={(e) =>
                                          this.setState({
                                            name: Utils.safeParseEventValue(e),
                                          })
                                        }
                                        isValid={name && name.length}
                                        type='text'
                                        inputClassName='input--wide'
                                        placeholder='My Organisation'
                                      />
                                    </Column>
                                    <Button
                                      type='submit'
                                      disabled={this.saveDisabled()}
                                      className='float-right'
                                    >
                                      {isSaving ? 'Saving' : 'Save'}
                                    </Button>
                                  </Row>
                                </form>
                                <div>
                                  <Row space className='mt-4'>
                                    <h5 className='m-b-0'>Organisation ID</h5>
                                  </Row>
                                  <p className='fs-small lh-sm'>
                                    {organisation.id}
                                  </p>
                                </div>
                                {paymentsEnabled && !isAWS && (
                                  <div className='plan plan--current flex-row m-t-2'>
                                    <div className='plan__prefix'>
                                      <img
                                        src='/static/images/nav-logo.svg'
                                        className='plan__prefix__image'
                                        alt='BT'
                                      />
                                    </div>
                                    <div className='plan__details flex flex-1'>
                                      <p className='fs-small lh-sm m-b-0'>
                                        Your plan
                                      </p>
                                      <h5 className='m-b-0'>
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
                                      </h5>
                                      {!!chargebee_email && (
                                        <p>
                                          Management Email:{' '}
                                          <strong>{chargebee_email}</strong>
                                        </p>
                                      )}
                                    </div>
                                    <div>
                                      {organisation.subscription && (
                                        <a
                                          className='btn btn-primary mr-2'
                                          href='https://flagsmith.chargebeeportal.com/'
                                          target='_blank'
                                          rel='noreferrer'
                                        >
                                          Manage Invoices
                                        </a>
                                      )}
                                      {organisation.subscription ? (
                                        <button
                                          disabled={
                                            !this.state.manageSubscriptionLoaded
                                          }
                                          type='button'
                                          className='btn btn-primary text-center ml-auto mt-2 mb-2'
                                          onClick={() => {
                                            if (this.state.chargebeeURL) {
                                              window.location =
                                                this.state.chargebeeURL
                                            } else {
                                              openModal(
                                                'Payment plans',
                                                <PaymentModal
                                                  viewOnly={false}
                                                />,
                                                'modal-lg',
                                              )
                                            }
                                          }}
                                        >
                                          Manage payment plan
                                        </button>
                                      ) : (
                                        <button
                                          type='button'
                                          className='btn btn-primary text-center ml-auto mt-2 mb-2'
                                          onClick={() =>
                                            openModal(
                                              'Payment Plans',
                                              <PaymentModal viewOnly={false} />,
                                              'modal-lg',
                                            )
                                          }
                                        >
                                          View plans
                                        </button>
                                      )}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          </FormGroup>
                          {Utils.getFlagsmithHasFeature('force_2fa') && (
                            <div>
                              <Row space className='mt-4'>
                                <h5 className='m-b-0'>Enforce 2FA</h5>
                                {!force2faPermission ? (
                                  <Tooltip
                                    title={
                                      <Switch
                                        checked={organisation.force_2fa}
                                        onChange={this.save2FA}
                                      />
                                    }
                                  >
                                    To access this feature please upgrade your
                                    account to scaleup or higher."
                                  </Tooltip>
                                ) : (
                                  <Switch
                                    checked={organisation.force_2fa}
                                    onChange={this.save2FA}
                                  />
                                )}
                              </Row>
                              <p className='fs-small lh-sm'>
                                Enabling this setting forces users within the
                                organisation to setup 2 factor security.
                              </p>
                            </div>
                          )}
                          {Utils.getFlagsmithHasFeature(
                            'restrict_project_create_to_admin',
                          ) && (
                            <FormGroup className='mt-4'>
                              <h5>Admin Settings</h5>
                              <div className='row'>
                                <div className='col-md-10'>
                                  <p className='fs-small lh-sm'>
                                    Only allow organisation admins to create
                                    projects
                                  </p>
                                </div>
                                <div className='col-md-2 text-right'>
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
                                </div>
                              </div>
                            </FormGroup>
                          )}
                          <FormGroup className='mt-4'>
                            <h5>Delete Organisation</h5>
                            <div className='row'>
                              <div className='col-md-10'>
                                <p className='fs-small lh-sm'>
                                  This organisation will be permanently deleted,
                                  along with all projects and features.
                                </p>
                              </div>
                              <div className='col-md-2 text-right'>
                                <Button
                                  id='delete-org-btn'
                                  onClick={() =>
                                    this.confirmRemove(organisation, () => {
                                      deleteOrganisation()
                                    })
                                  }
                                  className='btn btn--with-icon ml-auto btn--remove'
                                >
                                  <RemoveIcon />
                                </Button>
                              </div>
                            </div>
                          </FormGroup>
                        </TabItem>

                        <TabItem tabLabel='Keys'>
                          <AdminAPIKeys />
                        </TabItem>

                        <TabItem data-test='tab-permissions' tabLabel='Members'>
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
                            <h5>Manage Users and Permissions</h5>
                            <p className='fs-small lh-sm'>
                              Flagsmith lets you manage fine-grained permissions
                              for your projects and environments, invite members
                              as a user or an administrator and then set
                              permission in your Project and Environment
                              settings.{' '}
                              <Button
                                theme='text'
                                href='https://docs.flagsmith.com/system-administration/rbac'
                                target='_blank'
                              >
                                Learn about User Roles.
                              </Button>
                            </p>
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
                                      <Tabs theme='pill' uncontrolled>
                                        <TabItem tabLabel='Members'>
                                          <Row space className='mt-4'>
                                            <h5 className='m-b-0'>
                                              Team Members
                                            </h5>
                                            <Button
                                              disabled={
                                                needsUpgradeForAdditionalSeats
                                              }
                                              style={{ width: 180 }}
                                              id='btn-invite'
                                              onClick={() =>
                                                openModal(
                                                  'Invite Users',
                                                  <InviteUsersModal />,
                                                  'p-0 side-modal',
                                                )
                                              }
                                              type='button'
                                            >
                                              Invite members
                                            </Button>
                                          </Row>
                                          <FormGroup className='mt-2'>
                                            {paymentsEnabled && !isLoading && (
                                              <InfoMessage>
                                                {'You are currently using '}
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
                                                  organisation.num_seats === 1
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
                                                        If you wish to invite
                                                        any additional members,
                                                        please{' '}
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
                                                        If you wish to invite
                                                        any additional members,
                                                        please{' '}
                                                        {
                                                          <a
                                                            href='#'
                                                            onClick={() =>
                                                              openModal(
                                                                'Payment Plans',
                                                                <PaymentModal
                                                                  viewOnly={
                                                                    false
                                                                  }
                                                                />,
                                                                'modal-lg',
                                                              )
                                                            }
                                                          >
                                                            Upgrade your plan
                                                          </a>
                                                        }
                                                        .
                                                      </strong>
                                                    ) : (
                                                      <strong>
                                                        You will automatically
                                                        be charged $20/month for
                                                        each additional member
                                                        that joins your
                                                        organisation.
                                                      </strong>
                                                    )}
                                                  </>
                                                )}
                                              </InfoMessage>
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
                                                        className='mr-2'
                                                        style={{ width: 280 }}
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
                                                                width: '100%',
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
                                                              className='full-width'
                                                              type='text'
                                                              readonly='readonly'
                                                              title={
                                                                <h3>Link</h3>
                                                              }
                                                              placeholder='Link'
                                                            />
                                                          </Flex>
                                                          <Row>
                                                            <Button
                                                              className='btn-secondary'
                                                              style={{
                                                                width: 180,
                                                              }}
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
                                                              className='ml-4'
                                                              type='button'
                                                              onClick={() => {
                                                                openConfirm(
                                                                  'Regenerate Invite Link',
                                                                  'This will generate a new invite link for the selected role, users will no longer be able to use the existing one. Are you sure?',
                                                                  () => {
                                                                    invalidateInviteLink(
                                                                      inviteLinks.find(
                                                                        (f) =>
                                                                          f.role ===
                                                                          this
                                                                            .state
                                                                            .role,
                                                                      ),
                                                                    )
                                                                  },
                                                                )
                                                              }}
                                                            >
                                                              Regenerate
                                                            </Button>
                                                          </Row>
                                                        </>
                                                      )}
                                                    </Row>
                                                  </div>
                                                  <p className='mt-3'>
                                                    Anyone with link can join as
                                                    a standard user, once they
                                                    have joined you can edit
                                                    their role from the team
                                                    members panel.{' '}
                                                    <Button
                                                      theme='text'
                                                      target='_blank'
                                                      href='https://docs.flagsmith.com/advanced-use/permissions'
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
                                                  <Flex className='table-column'>
                                                    Role
                                                  </Flex>
                                                  <div
                                                    style={{ width: widths[0] }}
                                                    className='table-column'
                                                  >
                                                    Action
                                                  </div>
                                                  <div
                                                    style={{ width: widths[1] }}
                                                    className='table-column'
                                                  >
                                                    Last logged in
                                                  </div>
                                                  <div
                                                    style={{ width: widths[2] }}
                                                    className='table-column text-center'
                                                  >
                                                    Remove
                                                  </div>
                                                </Row>
                                              }
                                              items={_.sortBy(
                                                users,
                                                'first_name',
                                              )}
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
                                                const onEditClick = () => {
                                                  if (role !== 'ADMIN') {
                                                    this.editUserPermissions(
                                                      user,
                                                    )
                                                  }
                                                }
                                                return (
                                                  <Row
                                                    data-test={`user-${i}`}
                                                    space
                                                    className='list-item clickable'
                                                    key={id}
                                                  >
                                                    <Flex
                                                      onClick={onEditClick}
                                                      className='table-column px-3 font-weight-medium'
                                                    >
                                                      {`${first_name} ${last_name}`}{' '}
                                                      {id ===
                                                        AccountStore.getUserId() &&
                                                        '(You)'}
                                                      <div className='list-item-subtitle mt-1'>
                                                        {email}
                                                      </div>
                                                    </Flex>

                                                    <Flex className='table-column'>
                                                      <div>
                                                        {organisation.role ===
                                                          'ADMIN' &&
                                                        id !==
                                                          AccountStore.getUserId() ? (
                                                          <div>
                                                            <Select
                                                              data-test='select-role'
                                                              placeholder='Select a role'
                                                              styles={{
                                                                menuPortal: (
                                                                  base,
                                                                ) => ({
                                                                  ...base,
                                                                  zIndex: 9999,
                                                                }),
                                                              }}
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
                                                          <div className='mr-2 fs-small lh-sm'>
                                                            {Constants.roles[
                                                              role
                                                            ] || ''}
                                                          </div>
                                                        )}
                                                      </div>
                                                    </Flex>
                                                    {role !== 'ADMIN' ? (
                                                      <div
                                                        style={{
                                                          width: widths[0],
                                                        }}
                                                        onClick={onEditClick}
                                                        className='table-column'
                                                      >
                                                        <Button
                                                          theme='text'
                                                          size='small'
                                                        >
                                                          <Icon
                                                            name='edit'
                                                            width={18}
                                                            fill='#6837FC'
                                                          />{' '}
                                                          Edit Permissions
                                                        </Button>
                                                      </div>
                                                    ) : (
                                                      <div
                                                        style={{
                                                          width: widths[0],
                                                        }}
                                                      ></div>
                                                    )}
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
                                                      className='table-column text-center'
                                                    >
                                                      <Button
                                                        id='delete-invite'
                                                        type='button'
                                                        onClick={() =>
                                                          this.deleteUser(
                                                            id,
                                                            Format.userDisplayName(
                                                              {
                                                                email,
                                                                firstName:
                                                                  first_name,
                                                                lastName:
                                                                  last_name,
                                                              },
                                                            ),
                                                            email,
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
                                                      Action
                                                    </div>
                                                    <div
                                                      style={{
                                                        width: widths[2],
                                                      }}
                                                      className='table-column text-center'
                                                    >
                                                      Remove
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
                                                        ).format('DD/MMM/YYYY')}
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
                                                        width: widths[2],
                                                      }}
                                                    >
                                                      <Button
                                                        id='delete-invite'
                                                        type='button'
                                                        onClick={() =>
                                                          this.deleteInvite(id)
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
                                            <Row space className='mt-4'>
                                              <h5 className='m-b-0'>
                                                User Groups
                                              </h5>
                                              <Button
                                                className='mr-2'
                                                id='btn-invite'
                                                onClick={() =>
                                                  openModal(
                                                    'Create Group',
                                                    <CreateGroupModal
                                                      orgId={organisation.id}
                                                    />,
                                                    'side-modal',
                                                  )
                                                }
                                                type='button'
                                              >
                                                Create Group
                                              </Button>
                                            </Row>
                                            <p className='fs-small lh-sm'>
                                              Groups allow you to manage
                                              permissions for viewing and
                                              editing projects, features and
                                              environments.
                                            </p>
                                            <UserGroupList
                                              onEditPermissions={
                                                this.editGroupPermissions
                                              }
                                              showRemove
                                              orgId={
                                                organisation && organisation.id
                                              }
                                            />
                                          </div>
                                        </TabItem>
                                        {Utils.getFlagsmithHasFeature(
                                          'show_role_management',
                                        ) && (
                                          <TabItem tabLabel='Roles'>
                                            {hasRbacPermission ? (
                                              <>
                                                <Row space className='mt-4'>
                                                  <h5 className='m-b-0'>
                                                    Roles
                                                  </h5>
                                                  <Button
                                                    className='mr-2'
                                                    id='btn-invite'
                                                    onClick={() =>
                                                      this.createRole(
                                                        organisation.id,
                                                      )
                                                    }
                                                    type='button'
                                                  >
                                                    Create Role
                                                  </Button>
                                                </Row>
                                                <p className='fs-small lh-sm'>
                                                  Create custom roles, assign
                                                  permissions, and keys to the
                                                  role, and then you can assign
                                                  roles to users and/or groups.
                                                </p>
                                                <PanelSearch
                                                  id='org-members-list'
                                                  title={'Roles'}
                                                  className='no-pad'
                                                  items={roles}
                                                  itemHeight={65}
                                                  header={
                                                    <Row className='table-header px-3'>
                                                      <div
                                                        style={{
                                                          width: rolesWidths[0],
                                                        }}
                                                      >
                                                        Roles
                                                      </div>
                                                      <div
                                                        style={{
                                                          width: rolesWidths[1],
                                                        }}
                                                      >
                                                        Description
                                                      </div>
                                                      <div className='table-column text-center'>
                                                        Remove
                                                      </div>
                                                    </Row>
                                                  }
                                                  renderRow={(role) => (
                                                    <Row
                                                      className='list-item clickable cursor-pointer'
                                                      key={role.id}
                                                    >
                                                      <Row
                                                        onClick={() => {
                                                          this.editRole(role)
                                                        }}
                                                        className='table-column px-3'
                                                        style={{
                                                          width: rolesWidths[0],
                                                        }}
                                                      >
                                                        {role.name}
                                                      </Row>
                                                      <Row
                                                        className='table-column px-3'
                                                        onClick={() => {
                                                          this.editRole(role)
                                                        }}
                                                        style={{
                                                          width: rolesWidths[1],
                                                        }}
                                                      >
                                                        {role.description}
                                                      </Row>
                                                      <div
                                                        style={{
                                                          width: rolesWidths[2],
                                                        }}
                                                        className='table-column text-center px-3'
                                                      >
                                                        <Button
                                                          id='remove-role'
                                                          type='button'
                                                          onClick={() => {
                                                            this.deleteRole(
                                                              role,
                                                            )
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
                                                      title={
                                                        'Organisation roles'
                                                      }
                                                      className='no-pad'
                                                    >
                                                      <div className='search-list'>
                                                        <Row className='list-item p-3 text-muted'>
                                                          You currently have no
                                                          organisation roles
                                                        </Row>
                                                      </div>
                                                    </Panel>
                                                  }
                                                  isLoading={false}
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

                        <TabItem tabLabel='Webhooks'>
                          <FormGroup className='mt-4'>
                            <JSONReference title={'Webhooks'} json={webhooks} />

                            <Column className='mb-3 ml-0'>
                              <h5 className='m-b-0'>Audit Webhooks</h5>
                              <p className='fs-small lh-sm mb-4'>
                                Audit webhooks let you know when audit logs
                                occur, you can configure 1 or more audit
                                webhooks per organisation.{' '}
                                <Button
                                  theme='text'
                                  href='https://docs.flagsmith.com/system-administration/webhooks'
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
                        {!Project.disableAnalytics && (
                          <TabItem tabLabel='Usage'>
                            {this.state.tab === 4 && (
                              <OrganisationUsage
                                organisationId={
                                  AccountStore.getOrganisation().id
                                }
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
