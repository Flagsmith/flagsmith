import React, { Component } from 'react'
import ConfirmRemoveOrganisation from 'components/modals/ConfirmRemoveOrganisation'
import Payment from 'components/modals/Payment'
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
import SamlTab from 'components/SamlTab'
import Setting from 'components/Setting'
import AccountProvider from 'common/providers/AccountProvider'
import LicensingTabContent from 'components/LicensingTabContent'
import Utils from 'common/utils/utils'
import AuditLogWebhooks from 'components/modals/AuditLogWebhooks'
import MetadataPage from 'components/metadata/MetadataPage'
import { withRouter } from 'react-router-dom'
const SettingsTab = {
  'Billing': 'billing',
  'CustomFields': 'custom-fields',
  'General': 'general',
  'Keys': 'keys',
  'Licensing': 'licensing',
  'SAML': 'saml',
  'Usage': 'usage',
  'Webhooks': 'webhooks',
}

const OrganisationSettingsPage = class extends Component {
  static displayName = 'OrganisationSettingsPage'

  constructor(props) {
    super(props)
    this.state = {
      manageSubscriptionLoaded: true,
      permissions: [],
    }
    if (!AccountStore.getOrganisation()) {
      return
    }
    AppActions.getOrganisation(AccountStore.getOrganisation().id)

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
      this.props.history.replace(Utils.getOrganisationHomePage())
    } else {
      this.props.history.replace('/create')
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

  getOrganisationPermissions = (id) => {
    if (this.state.permissions.length) return

    const url = `${Project.api}organisations/${id}/my-permissions/`
    _data.get(url).then(({ permissions }) => {
      this.setState({ permissions })
    })
  }

  render() {
    const paymentsEnabled = Utils.getFlagsmithHasFeature('payments_enabled')

    return (
      <div className='app-container container'>
        <AccountProvider onSave={this.onSave} onRemove={this.onRemove}>
          {({ isSaving, organisation }, { deleteOrganisation }) =>
            !!organisation && (
              <OrganisationProvider id={AccountStore.getOrganisation()?.id}>
                {({ name, subscriptionMeta }) => {
                  const isAWS =
                    AccountStore.getPaymentMethod() === 'AWS_MARKETPLACE'
                  const { chargebee_email } = subscriptionMeta || {}

                  const displayedTabs = []
                  //todo: replace with RTK when this is a functional component
                  const isEnterprise = Utils.isEnterpriseImage()
                  if (
                    AccountStore.getUser() &&
                    AccountStore.getOrganisationRole() === 'ADMIN'
                  ) {
                    displayedTabs.push(
                      ...[
                        SettingsTab.General,
                        paymentsEnabled && !isAWS ? SettingsTab.Billing : null,
                        isEnterprise ? SettingsTab.Licensing : null,
                        SettingsTab.CustomFields,
                        SettingsTab.Keys,
                        SettingsTab.Webhooks,
                        SettingsTab.SAML,
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
                      <Tabs
                        hideNavOnSingleTab
                        urlParam='tab'
                        className='mt-0'
                        history={this.props.history}
                      >
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
                                <div className='col-md-8'>
                                  <Setting
                                    feature={'FORCE_2FA'}
                                    checked={organisation.force_2fa}
                                    onChange={this.save2FA}
                                  />
                                </div>
                                {Utils.getFlagsmithHasFeature(
                                  'restrict_project_create_to_admin',
                                ) && (
                                  <FormGroup className='mt-4 col-md-8'>
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
                            <FormGroup className='mt-4 col-md-8'>
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
                                      Manage subscription
                                    </Button>
                                  )}
                                </div>
                              </Row>
                              <h5>Manage Payment Plan</h5>
                              <Payment viewOnly={false} />
                            </div>
                          </TabItem>
                        )}

                        {displayedTabs.includes(SettingsTab.Licensing) && (
                          <TabItem tabLabel='Licensing'>
                            <LicensingTabContent
                              organisationId={organisation.id}
                            />
                          </TabItem>
                        )}
                        {displayedTabs.includes(SettingsTab.CustomFields) && (
                          <TabItem tabLabel='Custom Fields'>
                            <MetadataPage
                              organisationId={AccountStore.getOrganisation().id}
                            />
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
                              <AuditLogWebhooks
                                organisationId={
                                  AccountStore.getOrganisation().id
                                }
                              />
                            </FormGroup>
                          </TabItem>
                        )}
                        {displayedTabs.includes(SettingsTab.SAML) && (
                          <TabItem tabLabel='SAML'>
                            <SamlTab organisationId={organisation.id} />
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

export default withRouter(ConfigProvider(OrganisationSettingsPage))
