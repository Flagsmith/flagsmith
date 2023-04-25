import React, { Component } from 'react'
import InviteUsersModal from 'components/modals/InviteUsers'
import UserGroupList from 'components/UserGroupList'
import ConfirmRemoveOrganisation from 'components/modals/ConfirmRemoveOrganisation'
import PaymentModal from 'components/modals/Payment'
import CreateGroupModal from 'components/modals/CreateGroup'
import withAuditWebhooks from 'common/providers/withAuditWebhooks'
import CreateAuditWebhookModal from 'components/modals/CreateAuditWebhook'
import ConfirmRemoveAuditWebhook from 'components/modals/ConfirmRemoveAuditWebhook'
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

const widths = [450, 150, 100]
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
      'Remove Organisation',
      <ConfirmRemoveOrganisation organisation={organisation} cb={cb} />,
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
      <h3>Delete Invite</h3>,
      <p>Are you sure you want to delete this invite?</p>,
      () => AppActions.deleteInvite(id),
    )
  }

  deleteUser = (id) => {
    openConfirm(
      <h3>Delete User</h3>,
      <p>Are you sure you want to delete this user?</p>,
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
      null,
      { className: 'alert fade expand' },
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
      null,
      { className: 'alert fade expand' },
    )
  }

  deleteWebhook = (webhook) => {
    openModal(
      'Remove Webhook',
      <ConfirmRemoveAuditWebhook
        url={webhook.url}
        cb={() => this.props.deleteWebhook(webhook)}
      />,
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
    )
  }

  formatLastLoggedIn = (last_login) => {
    if (!last_login) return 'Never'

    const diff = moment().diff(moment(last_login), 'days')
    if (diff >= 30) {
      return (
        <>
          {`${diff} days ago`}
          <br />
          <span className='text-small text-muted'>
            {moment(last_login).format('Do MMM YYYY')}
          </span>
        </>
      )
    }
    return 'Within 30 days'
  }

  render() {
    const {
      props: { webhooks, webhooksLoading },
    } = this
    const hasRbacPermission = Utils.getPlansPermission('RBAC')
    const paymentsEnabled = Utils.getFlagsmithHasFeature('payments_enabled')
    const force2faPermission = Utils.getPlansPermission('FORCE_2FA')

    return (
      <div className='app-container container'>
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
                  subscriptionMeta,
                  users,
                }) => {
                  const { max_seats } = subscriptionMeta ||
                    organisation.subscription || { max_seats: 1 }
                  const autoSeats = Utils.getPlansPermission('AUTO_SEATS')
                  const usedSeats =
                    paymentsEnabled && organisation.num_seats >= max_seats
                  const overSeats =
                    paymentsEnabled && organisation.num_seats > max_seats
                  const needsUpgradeForAdditionalSeats =
                    overSeats || (!autoSeats && usedSeats)
                  return (
                    <div>
                      <Tabs
                        inline
                        transparent
                        value={this.state.tab || 0}
                        onChange={(tab) => this.setState({ tab })}
                      >
                        <TabItem tabLabel='General' tabIcon='ion-md-settings'>
                          <FormGroup>
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
                                    <Column className='m-l-0'>
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
                                      disabled={this.saveDisabled()}
                                      className='float-right'
                                    >
                                      {isSaving ? 'Saving' : 'Save'}
                                    </Button>
                                  </Row>
                                </form>
                                {paymentsEnabled && (
                                  <div className='plan plan--current flex-row m-t-2'>
                                    <div className='plan__prefix'>
                                      <img
                                        src='/static/images/nav-logo.svg'
                                        className='plan__prefix__image'
                                        alt='BT'
                                      />
                                    </div>
                                    <div className='plan__details flex flex-1'>
                                      <p className='text-small m-b-0'>
                                        Your plan
                                      </p>
                                      <h3 className='m-b-0'>
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
                                      </h3>
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
                                                null,
                                                { large: true },
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
                                              null,
                                              { large: true },
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
                                <h3 className='m-b-0'>Enforce 2FA</h3>
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
                              <p>
                                Enabling this setting forces users within the
                                organisation to setup 2 factor security.
                              </p>
                            </div>
                          )}
                          {Utils.getFlagsmithHasFeature(
                            'restrict_project_create_to_admin',
                          ) && (
                            <FormGroup className='mt-4'>
                              <Row>
                                <Column>
                                  <h3>Admin Settings</h3>
                                  <Row>
                                    Only allow organisation admins to create
                                    projects
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
                                  </Row>
                                </Column>
                              </Row>
                            </FormGroup>
                          )}
                          {Utils.getFlagsmithHasFeature(
                            'delete_organisation',
                          ) && (
                            <FormGroup className='mt-4'>
                              <Row className='mt-4' space>
                                <div className='col-md-8 pl-0'>
                                  <h3>Delete Organisation</h3>
                                  <p>
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
                                  className='btn btn--with-icon ml-auto btn--remove'
                                >
                                  <RemoveIcon />
                                </Button>
                              </Row>
                            </FormGroup>
                          )}
                        </TabItem>

                        <TabItem tabLabel='Keys' tabIcon='ion-md-key'>
                          <AdminAPIKeys />
                        </TabItem>

                        <TabItem
                          data-test='tab-permissions'
                          tabLabel='Members'
                          tabIcon='ion-md-people'
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
                            <h3>Manage Users and Permissions</h3>
                            <p>
                              Flagsmith lets you manage fine-grained permissions
                              for your projects and environments, invite members
                              as a user or an administrator and then set
                              permission in your Project and Environment
                              settings.{' '}
                              <ButtonLink
                                href='https://docs.flagsmith.com/advanced-use/permissions'
                                target='_blank'
                              >
                                Learn about User Roles.
                              </ButtonLink>
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
                                      <Tabs inline transparent uncontrolled>
                                        <TabItem tabLabel='Members'>
                                          <Row space className='mt-4'>
                                            <h3 className='m-b-0'>
                                              Team Members
                                            </h3>
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
                                                    {overSeats ? (
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
                                                                null,
                                                                { large: true },
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
                                            {inviteLinks && (
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
                                                            this.state.role ===
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
                                                              document.location
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
                                                                      this.state
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
                                                  Anyone with link can join as a
                                                  standard user, once they have
                                                  joined you can edit their role
                                                  from the team members panel.{' '}
                                                  <ButtonLink
                                                    target='_blank'
                                                    href='https://docs.flagsmith.com/advanced-use/permissions'
                                                  >
                                                    Learn about User Roles.
                                                  </ButtonLink>
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
                                                  <Flex>
                                                    <strong>User</strong>
                                                  </Flex>
                                                  <div
                                                    style={{ width: widths[0] }}
                                                  >
                                                    Role
                                                  </div>
                                                  <div
                                                    style={{ width: widths[1] }}
                                                  >
                                                    Last logged in
                                                  </div>
                                                  <div
                                                    style={{ width: widths[2] }}
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
                                                    <Flex onClick={onEditClick}>
                                                      {`${first_name} ${last_name}`}{' '}
                                                      {id ===
                                                        AccountStore.getUserId() &&
                                                        '(You)'}
                                                      <div className='list-item-footer faint'>
                                                        {email}
                                                      </div>
                                                    </Flex>

                                                    <Row
                                                      style={{
                                                        width: widths[0],
                                                      }}
                                                    >
                                                      <div>
                                                        {organisation.role ===
                                                          'ADMIN' &&
                                                        id !==
                                                          AccountStore.getUserId() ? (
                                                          <div
                                                            style={{
                                                              width: 250,
                                                            }}
                                                          >
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
                                                            />
                                                          </div>
                                                        ) : (
                                                          <div className='mr-2'>
                                                            {Constants.roles[
                                                              role
                                                            ] || ''}
                                                          </div>
                                                        )}
                                                      </div>

                                                      {role !== 'ADMIN' && (
                                                        <div
                                                          className='ml-2'
                                                          style={{
                                                            width: widths[2],
                                                          }}
                                                          onClick={onEditClick}
                                                        >
                                                          <Button className='btn--link'>
                                                            Edit Permissions
                                                          </Button>
                                                        </div>
                                                      )}
                                                    </Row>

                                                    <div
                                                      style={{
                                                        width: widths[1],
                                                      }}
                                                    >
                                                      <div>
                                                        {this.formatLastLoggedIn(
                                                          last_login,
                                                        )}
                                                      </div>
                                                    </div>
                                                    <div
                                                      style={{
                                                        width: widths[2],
                                                      }}
                                                    >
                                                      <button
                                                        id='delete-invite'
                                                        type='button'
                                                        onClick={() =>
                                                          this.deleteUser(id)
                                                        }
                                                        className='btn btn--with-icon ml-auto btn--remove'
                                                      >
                                                        <RemoveIcon />
                                                      </button>
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
                                                    <div className='flex flex-1'>
                                                      {email || link}
                                                      <div className='list-item-footer faint'>
                                                        Created{' '}
                                                        {moment(
                                                          date_created,
                                                        ).format('DD/MMM/YYYY')}
                                                      </div>
                                                      {invited_by ? (
                                                        <div className='list-item-footer faint'>
                                                          Invited by{' '}
                                                          {invited_by.first_name
                                                            ? `${invited_by.first_name} ${invited_by.last_name}`
                                                            : invited_by.email}
                                                        </div>
                                                      ) : null}
                                                    </div>
                                                    <Row>
                                                      <Column>
                                                        {link ? (
                                                          ' '
                                                        ) : (
                                                          <button
                                                            id='resend-invite'
                                                            type='button'
                                                            onClick={() =>
                                                              AppActions.resendInvite(
                                                                id,
                                                              )
                                                            }
                                                            className='btn btn--link'
                                                          >
                                                            Resend
                                                          </button>
                                                        )}
                                                      </Column>
                                                      <Column>
                                                        <button
                                                          id='delete-invite'
                                                          type='button'
                                                          onClick={() =>
                                                            this.deleteInvite(
                                                              id,
                                                            )
                                                          }
                                                          className='btn btn--with-icon ml-auto btn--remove'
                                                        >
                                                          <RemoveIcon />
                                                        </button>
                                                      </Column>
                                                    </Row>
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
                                              <h3 className='m-b-0'>
                                                User Groups
                                              </h3>
                                              <Button
                                                className='mr-2'
                                                id='btn-invite'
                                                onClick={() =>
                                                  openModal(
                                                    'Create Group',
                                                    <CreateGroupModal
                                                      orgId={organisation.id}
                                                    />,
                                                    null,
                                                    {
                                                      className:
                                                        'side-modal fade create-feature-modal in',
                                                    },
                                                  )
                                                }
                                                type='button'
                                              >
                                                Create Group
                                              </Button>
                                            </Row>
                                            <p>
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
                                      </Tabs>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          </FormGroup>
                        </TabItem>

                        <TabItem tabLabel='Webhooks' tabIcon='ion-md-cloud'>
                          <FormGroup className='mt-4'>
                            <JSONReference title={'Webhooks'} json={webhooks} />

                            <Row className='mb-3' space>
                              <h3 className='m-b-0'>Audit Webhooks</h3>
                              <Button onClick={this.createWebhook}>
                                Create audit webhook
                              </Button>
                            </Row>
                            <p>
                              Audit webhooks let you know when audit logs occur,
                              you can configure 1 or more audit webhooks per
                              organisation.{' '}
                              <ButtonLink href='https://docs.flagsmith.com/advanced-use/system-administration#audit-log-webhooks/'>
                                Learn about Audit Webhooks.
                              </ButtonLink>
                            </p>
                            {webhooksLoading && !webhooks ? (
                              <Loader />
                            ) : (
                              <PanelSearch
                                id='webhook-list'
                                title={
                                  <Tooltip
                                    title={
                                      <h6 className='mb-0'>
                                        Webhooks{' '}
                                        <span className='icon ion-ios-information-circle' />
                                      </h6>
                                    }
                                    place='right'
                                  >
                                    {Constants.strings.WEBHOOKS_DESCRIPTION}
                                  </Tooltip>
                                }
                                className='no-pad'
                                icon='ion-md-cloud'
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
                                    <div>
                                      <ButtonLink>{webhook.url}</ButtonLink>
                                      <div className='list-item-footer faint'>
                                        Created{' '}
                                        {moment(webhook.created_date).format(
                                          'DD/MMM/YYYY',
                                        )}
                                      </div>
                                    </div>
                                    <Row>
                                      <Switch checked={webhook.enabled} />
                                      <button
                                        id='delete-invite'
                                        type='button'
                                        onClick={(e) => {
                                          e.stopPropagation()
                                          e.preventDefault()
                                          this.deleteWebhook(webhook)
                                        }}
                                        className='btn btn--with-icon ml-auto btn--remove'
                                      >
                                        <RemoveIcon />
                                      </button>
                                    </Row>
                                  </Row>
                                )}
                                renderNoResults={
                                  <Panel
                                    icon='ion-md-cloud'
                                    title={
                                      <Tooltip
                                        title={
                                          <h6 className='mb-0'>
                                            Webhooks{' '}
                                            <span className='icon ion-ios-information-circle' />
                                          </h6>
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
                                    You currently have no webhooks configured
                                    for this organisation.
                                  </Panel>
                                }
                                isLoading={this.props.webhookLoading}
                              />
                            )}
                          </FormGroup>
                        </TabItem>
                        {Utils.getFlagsmithHasFeature('usage_chart') &&
                          (!Project.disableInflux ||
                            !Project.disableAnalytics) && (
                            <TabItem
                              tabLabel='Usage'
                              tabIcon='ion-md-analytics'
                            >
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
