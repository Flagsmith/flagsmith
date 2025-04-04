import React, { Component } from 'react'
import ConfirmRemoveEnvironment from 'components/modals/ConfirmRemoveEnvironment'
import ProjectStore from 'common/stores/project-store'
import ConfigProvider from 'common/providers/ConfigProvider'
import CreateWebhookModal from 'components/modals/CreateWebhook'
import ConfirmRemoveWebhook from 'components/modals/ConfirmRemoveWebhook'
import ConfirmToggleEnvFeature from 'components/modals/ConfirmToggleEnvFeature'
import EditPermissions from 'components/EditPermissions'
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
import { getRoleEnvironmentPermissions } from 'common/services/useRolePermission'
import AccountStore from 'common/stores/account-store'
import { Link } from 'react-router-dom'
import { enableFeatureVersioning } from 'common/services/useEnableFeatureVersioning'
import AddMetadataToEntity from 'components/metadata/AddMetadataToEntity'
import { getSupportedContentType } from 'common/services/useSupportedContentType'
import EnvironmentVersioningListener from 'components/EnvironmentVersioningListener'
import Format from 'common/utils/format'
import Setting from 'components/Setting'
import ChangeRequestsSetting from 'components/ChangeRequestsSetting'
import Utils from 'common/utils/utils'
import {
  createWebhook,
  deleteWebhook,
  getWebhooks,
  updateWebhook,
} from 'common/services/useWebhooks'

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
      webhooks: [],
      webhooksLoading: true,
    }
    AppActions.getProject(this.props.match.params.projectId)
  }

  componentDidMount = () => {
    API.trackPage(Constants.pages.ENVIRONMENT_SETTINGS)
    this.getEnvironment()
    this.fetchWebhooks(this.props.match.params.environmentId)
  }

  fetchWebhooks = (environmentId) => {
    if (!environmentId) return

    this.setState({ webhooksLoading: true })
    getWebhooks(getStore(), { environmentId })
      .then((res) => {
        this.setState({
          webhooks: res.data,
        })
      })
      .finally(() => {
        this.setState({ webhooksLoading: false })
      })
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
      if (!roles?.data?.results?.length) return

      getRoleEnvironmentPermissions(
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

    if (Utils.getPlansPermission('METADATA')) {
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
    this.fetchWebhooks(this.props.match.params.environmentId)
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

  onRemoveEnvironment = (environment) => {
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
    toast(
      <div>
        Removed Environment: <strong>{environment.name}</strong>
      </div>,
    )
  }

  saveEnv = (e) => {
    e && e.preventDefault()

    const env = _.find(ProjectStore.getEnvs(), {
      api_key: this.props.match.params.environmentId,
    })

    const { name } = this.state
    if (ProjectStore.isSaving || !name) {
      return
    }
    const has4EyesPermission = Utils.getPlansPermission('4_EYES')
    AppActions.editEnv(
      Object.assign({}, env, {
        allow_client_traits: !!this.state.allow_client_traits,
        banner_colour: this.state.banner_colour,
        banner_text: this.state.banner_text,
        description: this.state?.env?.description,
        hide_disabled_flags: this.state.hide_disabled_flags,
        hide_sensitive_data: !!this.state.hide_sensitive_data,
        minimum_change_request_approvals: has4EyesPermission
          ? this.state.minimum_change_request_approvals
          : null,
        name: name || env.name,
        use_identity_composite_key_for_hashing:
          !!this.state.use_identity_composite_key_for_hashing,
        use_identity_overrides_in_local_eval:
          this.state.use_identity_overrides_in_local_eval,
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
        save={(webhook) =>
          createWebhook(getStore(), {
            environmentId: this.props.match.params.environmentId,
            ...webhook,
          }).then((res) => {
            this.setState({
              webhooks: this.state.webhooks.concat(res.data),
            })
          })
        }
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
        save={(webhook) =>
          updateWebhook(getStore(), {
            environmentId: this.props.match.params.environmentId,
            ...webhook,
          }).then(() => {
            this.setState({
              webhooks: this.state.webhooks.map((w) =>
                w.id === webhook.id ? webhook : w,
              ),
            })
          })
        }
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
        cb={() =>
          deleteWebhook(getStore(), {
            environmentId: this.props.match.params.environmentId,
            id: webhook.id,
          }).then(() => {
            this.setState({
              webhooks: this.state.webhooks.filter((w) => w.id !== webhook.id),
            })
          })
        }
      />,
      'p-0',
    )
  }

  confirmToggle = (title, environmentProperty, environmentPropertyValue) => {
    openModal(
      title,
      <ConfirmToggleEnvFeature
        description={'Are you sure that you want to change this value?'}
        feature={Format.enumeration.get(environmentProperty)}
        featureValue={environmentPropertyValue}
        onToggleChange={() => {
          this.setState(
            { [environmentProperty]: !environmentPropertyValue },
            this.saveEnv,
          )
          closeModal()
        }}
      />,
      'p-0 modal-sm',
    )
  }

  render() {
    const {
      state: {
        allow_client_traits,
        hide_sensitive_data,
        name,
        use_identity_composite_key_for_hashing,
        use_identity_overrides_in_local_eval,
        use_v2_feature_versioning,
        webhooks,
        webhooksLoading,
      },
    } = this
    const has4EyesPermission = Utils.getPlansPermission('4_EYES')
    const metadataEnable = Utils.getPlansPermission('METADATA')

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
                  use_identity_overrides_in_local_eval:
                    !!env.use_identity_overrides_in_local_eval,
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
                        <div className='col-md-8'>
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
                              value={this.state?.env?.description ?? ''}
                              inputProps={{
                                className: 'input--wide textarea-lg',
                              }}
                              onChange={(e) =>
                                this.setState({
                                  env: {
                                    ...this.state.env,
                                    description: Utils.safeParseEventValue(e),
                                  },
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
                        <div className='col-md-8 mt-4'>
                          <Setting
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
                            checked={typeof this.state.banner_text === 'string'}
                            title={'Environment Banner'}
                            description={
                              <div>
                                This will show a banner whenever you view its
                                pages.
                                <br />
                                This is generally used to warn people that they
                                are viewing and editing a sensitive environment.
                              </div>
                            }
                          />
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
                            <div className='col-md-8 mt-4'>
                              {use_v2_feature_versioning === false && (
                                <EnvironmentVersioningListener
                                  id={env.api_key}
                                  versioningEnabled={use_v2_feature_versioning}
                                  onChange={() => {
                                    this.setState({
                                      use_v2_feature_versioning: true,
                                    })
                                  }}
                                />
                              )}

                              <Setting
                                title={'Feature Versioning'}
                                description={
                                  <div>
                                    Allows you to attach versions to updating
                                    feature values and segment overrides.
                                    <br />
                                    This setting may take up to a minute to take
                                    affect.
                                    <br />
                                    <div className='text-danger'>
                                      Enabling this is irreversible.
                                    </div>
                                  </div>
                                }
                                disabled={
                                  use_v2_feature_versioning ||
                                  this.state.enabledFeatureVersioning
                                }
                                data-test={
                                  use_v2_feature_versioning
                                    ? 'feature-versioning-enabled'
                                    : 'enable-versioning'
                                }
                                checked={use_v2_feature_versioning}
                                onChange={onEnableVersioning}
                              />
                            </div>
                          </div>
                        )}
                        <div className='col-md-8 mt-4'>
                          <Setting
                            title='Hide sensitive data'
                            checked={hide_sensitive_data}
                            onChange={(v) => {
                              this.confirmToggle(
                                'Confirm Environment Setting',
                                'hide_sensitive_data',
                                hide_sensitive_data,
                              )
                            }}
                            description={
                              <div>
                                Exclude sensitive data from endpoints returning
                                flags and identity information to the SDKs or
                                via our REST API.
                                <br />
                                For full information on the excluded fields see
                                documentation{' '}
                                <Button
                                  theme='text'
                                  href='https://docs.flagsmith.com/system-administration/security#hide-sensitive-data'
                                  target='_blank'
                                  className='fw-normal'
                                >
                                  here.
                                </Button>
                                <div className='text-danger'>
                                  Enabling this feature will change the response
                                  from the API and could break your existing
                                  code.
                                </div>
                              </div>
                            }
                          />
                        </div>
                        <ChangeRequestsSetting
                          feature='4_EYES'
                          isLoading={this.saveDisabled()}
                          value={this.state.minimum_change_request_approvals}
                          onSave={this.saveEnv}
                          onToggle={(v) =>
                            this.setState(
                              {
                                minimum_change_request_approvals: v,
                              },
                              this.saveEnv,
                            )
                          }
                          onChange={(v) => {
                            this.setState({
                              minimum_change_request_approvals: v,
                            })
                          }}
                        />
                        <hr className='py-0 my-4' />
                        <FormGroup className='mt-4 col-md-8'>
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
                        <div className='col-md-8'>
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
                              <Setting
                                title='Allow client SDKs to set user traits'
                                description={`Disabling this option will prevent client SDKs from using the client key from setting traits.`}
                                checked={allow_client_traits}
                                onChange={(v) => {
                                  this.setState(
                                    { allow_client_traits: v },
                                    this.saveEnv,
                                  )
                                }}
                              />
                            </div>
                            <div className='mt-4'>
                              <Setting
                                checked={use_identity_composite_key_for_hashing}
                                onChange={(v) => {
                                  this.setState(
                                    {
                                      use_identity_composite_key_for_hashing: v,
                                    },
                                    this.saveEnv,
                                  )
                                }}
                                title={`Use consistent hashing`}
                                description={
                                  <div>
                                    Enabling this setting will ensure that
                                    multivariate and percentage split
                                    evaluations made by the API are consistent
                                    with those made by local evaluation mode in
                                    our server side SDKs.
                                    <div className='text-danger'>
                                      Toggling this setting will mean that some
                                      users will start receiving different
                                      values for multivariate flags and flags
                                      with a percentage split segment override
                                      via the API / remote evaluation. Values
                                      received in local evaluation mode will not
                                      change.
                                    </div>
                                  </div>
                                }
                              />
                            </div>
                            <div className='mt-4'>
                              <Setting
                                title='Use identity overrides in local evaluation'
                                description={`This determines whether server-side SDKs running in local evaluation mode receive identity overrides in the environment document.`}
                                checked={use_identity_overrides_in_local_eval}
                                onChange={(v) => {
                                  this.setState(
                                    {
                                      use_identity_overrides_in_local_eval: v,
                                    },
                                    this.saveEnv,
                                  )
                                }}
                              />
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
                        <TabItem tabLabel='Custom Fields'>
                          <FormGroup className='mt-5 setting'>
                            <InputGroup
                              title={'Custom fields'}
                              tooltip={`${Constants.strings.TOOLTIP_METADATA_DESCRIPTION(
                                'environments',
                              )}`}
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

module.exports = ConfigProvider(EnvironmentSettingsPage)
