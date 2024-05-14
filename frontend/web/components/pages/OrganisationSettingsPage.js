import React, { Component } from 'react'
import ConfirmRemoveOrganisation from 'components/modals/ConfirmRemoveOrganisation'
import Payment from 'components/modals/Payment'
import withAuditWebhooks from 'common/providers/withAuditWebhooks'
import CreateAuditWebhookModal from 'components/modals/CreateAuditWebhook'
import ConfirmRemoveAuditWebhook from 'components/modals/ConfirmRemoveAuditWebhook'
import Button from 'components/base/forms/Button'
import AdminAPIKeys from 'components/AdminAPIKeys'
import Tabs from 'components/base/forms/Tabs'
import TabItem from 'components/base/forms/TabItem'
import JSONReference from 'components/JSONReference'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
import Icon from 'components/Icon'
import _data from 'common/data/base/_data'
import AccountStore from 'common/stores/account-store'
import PageTitle from 'components/PageTitle'

const SettingsTab = {
  'Billing': 'billing',
  'General': 'general',
  'Keys': 'keys',
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
    API.trackPage(Constants.pages.ORGANISATION_SETTINGS)
    $('body').trigger('click')
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
      this.context.router.history.replace(Utils.getOrganisationHomePage())
    } else {
      this.context.router.history.replace('/create')
    }
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
    const paymentsEnabled = Utils.getFlagsmithHasFeature('payments_enabled')
    const force2faPermission = Utils.getPlansPermission('FORCE_2FA')

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
                {({ name, subscriptionMeta }) => {
                  const isAWS =
                    AccountStore.getPaymentMethod() === 'AWS_MARKETPLACE'
                  const { chargebee_email } = subscriptionMeta || {}

                  const displayedTabs = []

                  if (
                    AccountStore.getUser() &&
                    AccountStore.getOrganisationRole() === 'ADMIN'
                  ) {
                    displayedTabs.push(
                      ...[
                        SettingsTab.General,
                        paymentsEnabled && !isAWS ? SettingsTab.Billing : null,
                        SettingsTab.Keys,
                        SettingsTab.Webhooks,
                      ].filter((v) => !!v),
                    )
                  } else {
                    return (
                      <div className='py-2'>
                        You do not have permission to view this page
                      </div>
                    )
                  }
                  return (
                    <div>
                      <PageTitle title={'Organisation Settings'} />
                      <Tabs hideNavOnSingleTab urlParam='tab' className='mt-0'>
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
                                    the organisation to setup 2 factor security.
                                  </p>
                                </div>
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
