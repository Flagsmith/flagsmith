import React, { Component } from 'react'
import ConfirmRemoveEnvironment from 'components/modals/ConfirmRemoveEnvironment'
import ProjectStore from 'common/stores/project-store'
import ConfigProvider from 'common/providers/ConfigProvider'
import withWebhooks from 'common/providers/withWebhooks'
import CreateWebhookModal from 'components/modals/CreateWebhook'
import ConfirmRemoveWebhook from 'components/modals/ConfirmRemoveWebhook'
import ConfirmToggleEnvFeature from 'components/modals/ConfirmToggleEnvFeature'
import EditPermissions from 'components/EditPermissions'
import ServerSideSDKKeys from 'components/ServerSideSDKKeys'
import Tabs from 'components/base/forms/Tabs'
import TabItem from 'components/base/forms/TabItem'
import JSONReference from 'components/JSONReference'
import ColourSelect from 'components/tags/ColourSelect'
import Constants from 'common/constants'
import Switch from 'components/Switch'
import Icon from 'components/Icon'
import PageTitle from 'components/PageTitle'
import { getStore } from 'common/store'
import { getRoles } from 'common/services/useRole'
import { getRolesEnvironmentPermissions } from 'common/services/useRolePermission'
import AccountStore from 'common/stores/account-store'
import { Link } from 'react-router-dom'
import { enableFeatureVersioning } from 'common/services/useEnableFeatureVersioning'
import AddMetadataToEntity from 'components/metadata/AddMetadataToEntity'
import { getSupportedContentType } from 'common/services/useSupportedContentType'
import EnvironmentVersioningListener from 'components/EnvironmentVersioningListener'

const showDisabledFlagOptions = [
  { label: 'Inherit from Project', value: null },
  { label: 'Disabled', value: false },
  { label: 'Enabled', value: true },
]

const EnvironmentSettingsPage = class extends Component {
  static displayName = 'EnvironmentSettingsPage'

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  constructor(props, context) {
    super(props, context)
    this.state = {
      env: {},
      environmentContentType: {},
      roles: [],
      showMetadataList: false,
    }
    AppActions.getProject(this.props.match.params.projectId)
  }

  componentDidMount = () => {
    API.trackPage(Constants.pages.ENVIRONMENT_SETTINGS)
    this.getEnvironment()
    this.props.getWebhooks()
  }

  getEnvironment = () => {
    const env = ProjectStore.getEnvs().find(
      (v) => v.api_key === this.props.match.params.environmentId,
    )
    this.setState({ env })
    getRoles(
      getStore(),
      { organisation_id: AccountStore.getOrganisation().id },
      { forceRefetch: true },
    ).then((roles) => {
      getRolesEnvironmentPermissions(
        getStore(),
        {
          env_id: env.id,
          organisation_id: AccountStore.getOrganisation().id,
          role_id: roles.data.results[0].id,
        },
        { forceRefetch: true },
      ).then((res) => {
        const matchingItems = roles.data.results.filter((item1) =>
          res.data.results.some((item2) => item2.role === item1.id),
        )
        this.setState({ roles: matchingItems })
      })
    })

    if (Utils.getFlagsmithHasFeature('enable_metadata')) {
      getSupportedContentType(getStore(), {
        organisation_id: AccountStore.getOrganisation().id,
      }).then((res) => {
        const environmentContentType = Utils.getContentType(
          res.data,
          'model',
          'environment',
        )
        this.setState({ environmentContentType: environmentContentType })
      })
    }
    this.props.getWebhooks()
  }

  onSave = () => {
    toast('Environment Saved')
  }

  componentDidUpdate(prevProps) {
    if (
      this.props.match.params.projectId !== prevProps.match.params.projectId
    ) {
      AppActions.getProject(this.props.match.params.projectId)
    }
    if (
      this.props.match.params.environmentId !==
      prevProps.match.params.environmentId
    ) {
      this.getEnvironment()
    }
  }

  onRemove = () => {
    toast('Your project has been removed')
    this.context.router.history.replace(Utils.getOrganisationHomePage())
  }

  confirmRemove = (environment, cb) => {
    openModal(
      'Remove Environment',
      <ConfirmRemoveEnvironment environment={environment} cb={cb} />,
      'p-0',
    )
  }

  onRemoveEnvironment = () => {
    const envs = ProjectStore.getEnvs()
    if (envs && envs.length) {
      this.context.router.history.replace(
        `/project/${this.props.match.params.projectId}/environment` +
          `/${envs[0].api_key}/features`,
      )
    } else {
      this.context.router.history.replace(
        `/project/${this.props.match.params.projectId}/environment/create`,
      )
    }
  }

  saveEnv = (e) => {
    e && e.preventDefault()

    const env = _.find(ProjectStore.getEnvs(), {
      api_key: this.props.match.params.environmentId,
    })

    const { description, name } = this.state
    if (ProjectStore.isSaving || !name) {
      return
    }
    const has4EyesPermission = Utils.getPlansPermission('4_EYES')
    AppActions.editEnv(
      Object.assign({}, env, {
        allow_client_traits: !!this.state.allow_client_traits,
        banner_colour: this.state.banner_colour,
        banner_text: this.state.banner_text,
        description: description || env.description,
        hide_disabled_flags: this.state.hide_disabled_flags,
        hide_sensitive_data: !!this.state.hide_sensitive_data,
        minimum_change_request_approvals: has4EyesPermission
          ? this.state.minimum_change_request_approvals
          : null,
        name: name || env.name,
        use_identity_composite_key_for_hashing:
          !!this.state.use_identity_composite_key_for_hashing,
        use_mv_v2_evaluation: !!this.state.use_mv_v2_evaluation,
      }),
    )
  }

  saveDisabled = () => {
    const { name } = this.state
    if (ProjectStore.isSaving || !name) {
      return true
    }

    // Must have name
    return !name
  }

  createWebhook = () => {
    openModal(
      'New Webhook',
      <CreateWebhookModal
        router={this.context.router}
        environmentId={this.props.match.params.environmentId}
        projectId={this.props.match.params.projectId}
        save={this.props.createWebhook}
      />,
      'side-modal',
    )
  }

  editWebhook = (webhook) => {
    openModal(
      'Edit Webhook',
      <CreateWebhookModal
        router={this.context.router}
        webhook={webhook}
        isEdit
        environmentId={this.props.match.params.environmentId}
        projectId={this.props.match.params.projectId}
        save={this.props.saveWebhook}
      />,
      'side-modal',
    )
  }

  deleteWebhook = (webhook) => {
    openModal(
      'Remove Webhook',
      <ConfirmRemoveWebhook
        environmentId={this.props.match.params.environmentId}
        projectId={this.props.match.params.projectId}
        url={webhook.url}
        cb={() => this.props.deleteWebhook(webhook)}
      />,
      'p-0',
    )
  }

  confirmToggle = (title, description, feature) => {
    openModal(
      title,
      <ConfirmToggleEnvFeature
        description={`${description} Are you sure that you want to change this value?`}
        feature={feature}
        featureValue={this.state[feature]}
        onToggleChange={(value) => {
          this.setState({ [feature]: value }, this.saveEnv)
          closeModal()
        }}
      />,
      'p-0 modal-sm',
    )
  }

  render() {
    const {
      props: { webhooks, webhooksLoading },
      state: {
        allow_client_traits,
        hide_sensitive_data,
        name,
        use_identity_composite_key_for_hashing,
        use_v2_feature_versioning,
      },
    } = this
    const has4EyesPermission = Utils.getPlansPermission('4_EYES')
    const metadataEnable = Utils.getFlagsmithHasFeature('enable_metadata')

    return (
      <div className='app-container container'>
        <ProjectProvider
          onRemoveEnvironment={this.onRemoveEnvironment}
          id={this.props.match.params.projectId}
          onRemove={this.onRemove}
          onSave={this.onSave}
        >
          {({ deleteEnv, isLoading, isSaving, project }) => {
            const env = _.find(project.environments, {
              api_key: this.props.match.params.environmentId,
            })
            if (
              (env &&
                typeof this.state.minimum_change_request_approvals ===
                  'undefined') ||
              this.state.env?.api_key !== this.props.match.params.environmentId
            ) {
              setTimeout(() => {
                this.setState({
                  allow_client_traits: !!env.allow_client_traits,
                  banner_colour: env.banner_colour || Constants.tagColors[0],
                  banner_text: env.banner_text,
                  hide_disabled_flags: env.hide_disabled_flags,
                  hide_sensitive_data: !!env.hide_sensitive_data,
                  minimum_change_request_approvals: Utils.changeRequestsEnabled(
                    env.minimum_change_request_approvals,
                  )
                    ? env.minimum_change_request_approvals
                    : null,
                  name: env.name,
                  use_identity_composite_key_for_hashing:
                    !!env.use_identity_composite_key_for_hashing,
                  use_v2_feature_versioning: !!env.use_v2_feature_versioning,
                })
              }, 10)
            }
            const onEnableVersioning = () => {
              openConfirm({
                body: 'This will allow you to attach versions to updating feature values and segment overrides. Note: this may take several minutes to process',
                onYes: () => {
                  enableFeatureVersioning(getStore(), {
                    environmentId: env.api_key,
                  }).then((res) => {
                    toast(
                      'Feature Versioning Enabled, this may take several minutes to process.',
                    )
                    this.setState({
                      enabledFeatureVersioning: true,
                    })
                  })
                },
                title: 'Enable "Feature Versioning"',
              })
            }
            return (
              <>
                <PageTitle title='Settings' />
                {isLoading && (
                  <div className='centered-container'>
                    <Loader />
                  </div>
                )}
                {!isLoading && (
                  <Tabs urlParam='tab' className='mt-0' uncontrolled>
                    <TabItem tabLabel='General'>
                      <div className='mt-4'>
                        <h5 className='mb-5'>General Settings</h5>
                        <JSONReference title={'Environment'} json={env} />
                        <div className='col-md-6'>
                          <form onSubmit={this.saveEnv}>
                            <InputGroup
                              ref={(e) => (this.input = e)}
                              value={
                                typeof this.state.name === 'string'
                                  ? this.state.name
                                  : env.name
                              }
                              inputProps={{
                                className: 'full-width',
                                name: 'env-name',
                              }}
                              className='full-width'
                              onChange={(e) =>
                                this.setState({
                                  name: Utils.safeParseEventValue(e),
                                })
                              }
                              isValid={name && name.length}
                              type='text'
                              title='Environment Name'
                              placeholder='Environment Name'
                            />
                            <InputGroup
                              textarea
                              ref={(e) => (this.input = e)}
                              value={
                                typeof this.state.description === 'string'
                                  ? this.state.description
                                  : env.description
                              }
                              inputProps={{
                                className: 'input--wide textarea-lg',
                              }}
                              onChange={(e) =>
                                this.setState({
                                  description: Utils.safeParseEventValue(e),
                                })
                              }
                              isValid={name && name.length}
                              type='text'
                              title='Environment Description'
                              placeholder='Environment Description'
                            />
                            <div className='text-right mt-5'>
                              <Button
                                id='save-env-btn'
                                type='submit'
                                disabled={this.saveDisabled()}
                              >
                                {isSaving ? 'Updating' : 'Update'}
                              </Button>
                            </div>
                          </form>
                        </div>
                        <hr className='py-0 my-4' />
                        <div className='col-md-6 mt-4'>
                          <Row className='mb-2'>
                            <Switch
                              onChange={(value) =>
                                this.setState(
                                  {
                                    banner_text: value
                                      ? `${env.name} Environment`
                                      : null,
                                  },
                                  this.saveEnv,
                                )
                              }
                              checked={
                                typeof this.state.banner_text === 'string'
                              }
                            />
                            <h5 className='mb-0 ml-3'>Environment Banner</h5>
                          </Row>
                          <p className='fs-small lh-sm mb-0'>
                            This will show a banner whenever you view its pages,
                            this is generally used to warn people that they are
                            viewing and editing a sensitive environment.
                          </p>
                          {typeof this.state.banner_text === 'string' && (
                            <Row className='mt-4 flex-nowrap'>
                              <Input
                                placeholder='Banner text'
                                value={this.state.banner_text}
                                onChange={(e) =>
                                  this.setState({
                                    banner_text: Utils.safeParseEventValue(e),
                                  })
                                }
                                className='full-width'
                              />
                              <div className='ml-2'>
                                <ColourSelect
                                  value={this.state.banner_colour}
                                  onChange={(banner_colour) =>
                                    this.setState({ banner_colour })
                                  }
                                />
                              </div>
                              <Button onClick={this.saveEnv} size='small'>
                                Save
                              </Button>
                            </Row>
                          )}
                        </div>
                        {Utils.getFlagsmithHasFeature('feature_versioning') && (
                          <div>
                            <div className='col-md-6 mt-4'>
                              <EnvironmentVersioningListener
                                id={env.api_key}
                                versioningEnabled={use_v2_feature_versioning}
                                onChange={() => {
                                  this.setState({
                                    use_v2_feature_versioning: true,
                                  })
                                }}
                              />
                              <Row>
                                <Switch
                                  data-test={
                                    use_v2_feature_versioning
                                      ? 'feature-versioning-enabled'
                                      : 'enable-versioning'
                                  }
                                  disabled={
                                    use_v2_feature_versioning ||
                                    this.state.enabledFeatureVersioning
                                  }
                                  className='float-right'
                                  checked={use_v2_feature_versioning}
                                  onChange={onEnableVersioning}
                                />
                                <h5 className='mb-0 ml-3'>
                                  Feature versioning
                                </h5>
                              </Row>

                              <p className='fs-small lh-sm'>
                                Allows you to attach versions to updating
                                feature values and segment overrides. This
                                setting may take up to a minute to take affect.
                                <br />
                                <strong>
                                  Warning! Enabling this is irreversable
                                </strong>
                              </p>
                            </div>
                          </div>
                        )}
                        <div className='col-md-6 mt-4'>
                          <Row className='mb-2'>
                            <Switch
                              checked={hide_sensitive_data}
                              onChange={(v) => {
                                this.confirmToggle(
                                  'The data returned from the API will change and could break your existing code. Are you sure that you want to change this value?',
                                  'hide_sensitive_data',
                                  hide_sensitive_data,
                                )
                              }}
                            />
                            <h5 className='mb-0 ml-3'>Hide sensitive data</h5>
                          </Row>
                          <p className='fs-small lh-sm'>
                            Exclude sensitive data from endpoints returning
                            flags and identity information to the SDKs or via
                            our REST API. For full information on the excluded
                            fields see documentation{' '}
                            <Button
                              theme='text'
                              href='https://docs.flagsmith.com/system-administration/security#hide-sensitive-data'
                              target='_blank'
                              className='fw-normal'
                            >
                              here.
                            </Button>
                            <div className='text-danger'>
                              Warning! Enabling this feature will change the
                              response from the API and could break your
                              existing code.
                            </div>
                          </p>
                        </div>
                        <FormGroup className='mt-4 col-md-6'>
                          <Row className='mb-2'>
                            <Switch
                              className='float-right'
                              disabled={!has4EyesPermission}
                              checked={
                                has4EyesPermission &&
                                Utils.changeRequestsEnabled(
                                  this.state.minimum_change_request_approvals,
                                )
                              }
                              onChange={(v) =>
                                this.setState(
                                  {
                                    minimum_change_request_approvals: v
                                      ? 0
                                      : null,
                                  },
                                  this.saveEnv,
                                )
                              }
                            />
                            <h5 className='mb-0 ml-3'>Change Requests</h5>
                          </Row>
                          {!has4EyesPermission ? (
                            <p className='fs-small lh-sm'>
                              View and manage your feature changes with a Change
                              Request flow with our{' '}
                              <Link
                                to={Constants.upgradeURL}
                                className='btn-link'
                              >
                                Scale-up plan
                              </Link>
                              . Find out more{' '}
                              <Button
                                theme='text'
                                href='https://docs.flagsmith.com/advanced-use/change-requests'
                                target='_blank'
                              >
                                here
                              </Button>
                              .
                            </p>
                          ) : (
                            <p className='fs-small lh-sm mb-0'>
                              Require a minimum number of people to approve
                              changes to features.{' '}
                              <Button
                                theme='text'
                                href='https://docs.flagsmith.com/advanced-use/change-requests'
                                target='_blank'
                                className='fw-normal'
                              >
                                Learn about Change Requests.
                              </Button>
                            </p>
                          )}

                          {Utils.changeRequestsEnabled(
                            this.state.minimum_change_request_approvals,
                          ) &&
                            has4EyesPermission && (
                              <div className='mt-4'>
                                <div className='mb-2'>
                                  <strong>Minimum number of approvals</strong>
                                </div>
                                <Row>
                                  <Flex>
                                    <Input
                                      ref={(e) => (this.input = e)}
                                      value={`${this.state.minimum_change_request_approvals}`}
                                      inputClassName='input input--wide'
                                      name='env-name'
                                      min={0}
                                      style={{ minWidth: 50 }}
                                      onChange={(e) => {
                                        if (!Utils.safeParseEventValue(e))
                                          return
                                        this.setState({
                                          minimum_change_request_approvals:
                                            parseInt(
                                              Utils.safeParseEventValue(e),
                                            ),
                                        })
                                      }}
                                      isValid={name && name.length}
                                      type='number'
                                      placeholder='Minimum number of approvals'
                                    />
                                  </Flex>
                                  <Button
                                    type='button'
                                    onClick={this.saveEnv}
                                    id='save-env-btn'
                                    className='ml-3'
                                    disabled={
                                      this.saveDisabled() ||
                                      isSaving ||
                                      isLoading
                                    }
                                  >
                                    {isSaving || isLoading ? 'Saving' : 'Save'}
                                  </Button>
                                </Row>
                              </div>
                            )}
                        </FormGroup>
                        <hr className='py-0 my-4' />
                        <FormGroup className='mt-4 col-md-6'>
                          <Row space>
                            <div className='col-md-7'>
                              <h5>Delete Environment</h5>
                              <p className='fs-small lh-sm mb-0'>
                                This environment will be permanently deleted.
                              </p>
                            </div>
                            <Button
                              id='delete-env-btn'
                              onClick={() =>
                                this.confirmRemove(
                                  _.find(project.environments, {
                                    api_key:
                                      this.props.match.params.environmentId,
                                  }),
                                  () => {
                                    deleteEnv(
                                      _.find(project.environments, {
                                        api_key:
                                          this.props.match.params.environmentId,
                                      }),
                                    )
                                  },
                                )
                              }
                              className='btn btn-with-icon btn-remove'
                            >
                              <Icon name='trash-2' width={20} fill='#EF4D56' />
                            </Button>
                          </Row>
                        </FormGroup>
                      </div>
                    </TabItem>
                    <TabItem
                      data-test='js-sdk-settings'
                      tabLabel='SDK Settings'
                    >
                      <div className='mt-4'>
                        <JSONReference
                          title={'Environment'}
                          json={env}
                          className='mb-4'
                        />
                        <div className='col-md-6'>
                          <form onSubmit={this.saveEnv}>
                            <div>
                              <h5 className='mb-2'>
                                Hide disabled flags from SDKs
                              </h5>
                              <Select
                                value={
                                  showDisabledFlagOptions.find(
                                    (v) =>
                                      v.value ===
                                      this.state.hide_disabled_flags,
                                  ) || showDisabledFlagOptions[0]
                                }
                                onChange={(v) => {
                                  this.setState(
                                    { hide_disabled_flags: v.value },
                                    this.saveEnv,
                                  )
                                }}
                                options={showDisabledFlagOptions}
                                data-test='js-hide-disabled-flags'
                                disabled={isSaving}
                                className='full-width react-select mb-2'
                              />
                              <p className='mb-0 fs-small lh-sm'>
                                To prevent letting your users know about your
                                upcoming features and to cut down on payload,
                                enabling this will prevent the API from
                                returning features that are disabled. You can
                                also manage this in{' '}
                                <Link
                                  to={`/project/${this.props.match.params.projectId}/settings`}
                                >
                                  Project settings
                                </Link>
                                .
                              </p>
                            </div>
                            <div className='mt-4'>
                              <Row className='mb-2'>
                                <Switch
                                  checked={allow_client_traits}
                                  onChange={(v) => {
                                    this.setState(
                                      { allow_client_traits: v },
                                      this.saveEnv,
                                    )
                                  }}
                                />
                                <h5 className='mb-0 ml-3'>
                                  Allow client SDKs to set user traits
                                </h5>
                              </Row>
                              <p className='fs-small lh-sm mb-0'>
                                Disabling this option will prevent client SDKs
                                from using the client key from setting traits.
                              </p>
                            </div>
                            <div className='mt-4'>
                              <Row className='mb-2'>
                                <Switch
                                  checked={
                                    use_identity_composite_key_for_hashing
                                  }
                                  onChange={(v) => {
                                    this.setState(
                                      {
                                        use_identity_composite_key_for_hashing:
                                          v,
                                      },
                                      this.saveEnv,
                                    )
                                  }}
                                />
                                <h5 className='mb-0 ml-3'>
                                  Use Consistent Hashing
                                </h5>
                              </Row>
                              <p className='fs-small lh-sm'>
                                Enabling this setting will ensure that
                                multivariate and percentage split evaluations
                                made by the API are consistent with those made
                                by local evaluation mode in our server side
                                SDKs.
                                <div className='text-danger'>
                                  Warning: Toggling this setting will mean that
                                  some users will start receiving different
                                  values for multivariate flags and flags with a
                                  percentage split segment override via the API
                                  / remote evaluation. Values received in local
                                  evaluation mode will not change.
                                </div>
                              </p>
                            </div>
                          </form>
                        </div>
                      </div>
                    </TabItem>
                    <TabItem tabLabel='Permissions'>
                      <FormGroup>
                        <EditPermissions
                          tabClassName='flat-panel'
                          parentId={this.props.match.params.projectId}
                          parentLevel='project'
                          parentSettingsLink={`/project/${this.props.match.params.projectId}/settings`}
                          id={this.props.match.params.environmentId}
                          envId={env.id}
                          router={this.context.router}
                          level='environment'
                          roleTabTitle='Environment Permissions'
                          roles={this.state.roles}
                        />
                      </FormGroup>
                    </TabItem>
                    <TabItem tabLabel='Webhooks'>
                      <hr className='py-0 my-4' />
                      <FormGroup className='mt-4'>
                        <div className='col-md-8'>
                          <h5 className='mb-2'>Feature Webhooks</h5>
                          <p className='fs-small lh-sm mb-4'>
                            Feature webhooks let you know when features have
                            changed. You can configure 1 or more Feature
                            Webhooks per Environment.{' '}
                            <Button
                              theme='text'
                              href='https://docs.flagsmith.com/system-administration/webhooks#environment-web-hooks'
                              target='_blank'
                              className='fw-normal'
                            >
                              Learn about Feature Webhooks.
                            </Button>
                          </p>
                        </div>
                        <Button onClick={this.createWebhook}>
                          Create feature webhook
                        </Button>
                        <hr className='py-0 my-4' />
                        {webhooksLoading && !webhooks ? (
                          <Loader />
                        ) : (
                          <PanelSearch
                            id='webhook-list'
                            title={
                              <Tooltip
                                title={
                                  <h5 className='mb-0'>
                                    Webhooks <Icon name='info-outlined' />
                                  </h5>
                                }
                                place='right'
                              >
                                {Constants.strings.WEBHOOKS_DESCRIPTION}
                              </Tooltip>
                            }
                            className='no-pad'
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
                                  <div className='list-item-subtitle'>
                                    Created{' '}
                                    {moment(webhook.created_at).format(
                                      'DD/MMM/YYYY',
                                    )}
                                  </div>
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
                                id='users-list'
                                className='no-pad'
                                title={
                                  <Tooltip
                                    title={
                                      <h5 className='mb-0'>
                                        Webhooks <Icon name='info-outlined' />
                                      </h5>
                                    }
                                    place='right'
                                  >
                                    {Constants.strings.WEBHOOKS_DESCRIPTION}
                                  </Tooltip>
                                }
                              >
                                <div className='search-list'>
                                  <Row className='list-item p-3 text-muted'>
                                    You currently have no Feature Webhooks
                                    configured for this Environment.
                                  </Row>
                                </div>
                              </Panel>
                            }
                            isLoading={this.props.webhookLoading}
                          />
                        )}
                      </FormGroup>
                    </TabItem>
                    {metadataEnable &&
                      this.state.environmentContentType?.id && (
                        <TabItem tabLabel='Metadata'>
                          <FormGroup className='mt-5 setting'>
                            <InputGroup
                              title={'Metadata'}
                              tooltip={`${Constants.strings.TOOLTIP_METADATA_DESCRIPTION} environments`}
                              tooltipPlace='right'
                              component={
                                <AddMetadataToEntity
                                  organisationId={
                                    AccountStore.getOrganisation().id
                                  }
                                  projectId={this.props.match.params.projectId}
                                  entityId={env.api_key || ''}
                                  envName={env.name}
                                  entityContentType={
                                    this.state.environmentContentType.id
                                  }
                                  entity={
                                    this.state.environmentContentType.model
                                  }
                                />
                              }
                            />
                          </FormGroup>
                        </TabItem>
                      )}
                  </Tabs>
                )}
              </>
            )
          }}
        </ProjectProvider>
      </div>
    )
  }
}

EnvironmentSettingsPage.propTypes = {}

module.exports = ConfigProvider(withWebhooks(EnvironmentSettingsPage))
