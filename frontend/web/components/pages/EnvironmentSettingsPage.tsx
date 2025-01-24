import React, { Component, useEffect, useState, useMemo, useRef } from 'react'
import ConfirmRemoveEnvironment from 'components/modals/ConfirmRemoveEnvironment'
import ProjectStore from 'common/stores/project-store'
import ConfigProvider from 'common/providers/ConfigProvider'
import withWebhooks from 'common/providers/withWebhooks'
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
import _ from 'lodash'
import PageTitle from 'components/PageTitle'
import { getStore } from 'common/store'
import { getRoles } from 'common/services/useRole'
import { getRoleEnvironmentPermissions } from 'common/services/useRolePermission'
import AccountStore from 'common/stores/account-store'
import { Link, RouterChildContext } from 'react-router-dom'
import { enableFeatureVersioning } from 'common/services/useEnableFeatureVersioning'
import AddMetadataToEntity from 'components/metadata/AddMetadataToEntity'
import { getSupportedContentType } from 'common/services/useSupportedContentType'
import EnvironmentVersioningListener from 'components/EnvironmentVersioningListener'
import Format from 'common/utils/format'
import Setting from 'components/Setting'
import { useWebhooks } from 'components/hooks/useWebhooks'
import API from 'project/api'
import AppActions from 'common/dispatcher/app-actions'
import { Environment } from 'common/types/responses'
import PanelSearch from 'components/PanelSearch'
import moment from 'moment'
import Panel from 'components/base/grid/Panel'
import ProjectProvider from 'common/providers/ProjectProvider'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
type WebhookType = {
  id: string
  url: string
  secret: string
  enabled: boolean
  created_at: string
}

const showDisabledFlagOptions = [
  { label: 'Inherit from Project', value: null },
  { label: 'Disabled', value: false },
  { label: 'Enabled', value: true },
]

interface EnvironmentSettingsPageProps {
  // Router props
  match: {
    params: {
      projectId: string
      environmentId: string
    }
  }

  // Webhook props from HOC
  webhooks: WebhookType[]
  webhooksLoading: boolean
  getWebhooks: () => void
  createWebhook: (webhook: Partial<WebhookType>) => Promise<void>
  saveWebhook: (webhook: WebhookType) => Promise<void>
  deleteWebhook: (webhook: WebhookType) => Promise<void>
  // ConfigProvider props
  error?: any
  getValue?: (key: string) => any
  hasFeature?: (key: string) => boolean
}

const EnvironmentSettingsPageTS: React.FC<EnvironmentSettingsPageProps> = ({ createWebhook, deleteWebhook, getWebhooks, match, router, saveWebhook, webhooks, webhooksLoading }) => {
  // TODO: Improve Environment type
  const [currentEnv, setCurrentEnv] = useState<Environment | null>(null)
  const [myName, setMyName] = useState<string | null>(null)
  const [roles, setRoles] = useState<any[]>([])
  const [environmentContentType, setEnvironmentContentType] = useState<any>(null)
const inputRef = useRef<HTMLInputElement | null>(null)
  const store = getStore()


  const has4EyesPermission = Utils.getPlansPermission('4_EYES')
  const metadataEnable = Utils.getPlansPermission('METADATA')

  useEffect(() => {
    AppActions.getProject(match.params.projectId)
    console.log('yiha')
  }, [match.params.projectId])

  useEffect(() => {
    getEnvironment()
    console.log('plop')
  }, [match.params.environmentId])

  useEffect(() => {
    API.trackPage(Constants.pages.ENVIRONMENT_SETTINGS)
    getEnvironment()
    getWebhooks()
    console.log('yala')
  }, [])

  // TODO: types
  const getEnvironment = async () => {
    console.log('getEnvironment')
    const env = ProjectStore?.getEnvs()?.find(
      (v) => v.api_key === match.params.environmentId,
    )
    setCurrentEnv(env)

    const roles = await getRoles(
      store,
      { organisation_id: AccountStore.getOrganisation().id },
      { forceRefetch: true },
    )
    if (!roles?.data?.results?.length) return

    const roleEnvironmentPermissions = await getRoleEnvironmentPermissions(
      store,
      {
        env_id: env.id,
        organisation_id: AccountStore.getOrganisation().id,
        role_id: roles.data.results[0].id,
      },
      { forceRefetch: true },
    )

    const matchingItems = roles.data.results.filter((item1) =>
      roleEnvironmentPermissions.data.results.some((item2) => item2.role === item1.id),
    )
    setRoles(matchingItems)


    if (Utils.getPlansPermission('METADATA')) {
      const supportedContentType = await getSupportedContentType(getStore(), {
        organisation_id: AccountStore.getOrganisation().id,
      })
      const environmentContentType = Utils.getContentType(
        supportedContentType.data,
        'model',
        'environment',
      )
      setEnvironmentContentType(environmentContentType)
    }

    await getWebhooks()
  }

  const onSave = () => {
    toast('Environment Saved')
  }
  console.log('currentEnv', currentEnv)
  const onRemove = () => {
    toast('Your project has been removed')
    router.history.replace(Utils.getOrganisationHomePage())
  }

  const confirmRemove = (environment: Environment, callback: () => void) => {
    openModal(
      'Remove Environment',
      <ConfirmRemoveEnvironment environment={environment} cb={callback} />,
      'p-0',
    )
  }


  const onRemoveEnvironment = (environment: Environment) => {
    const envs = ProjectStore.getEnvs() as Environment[] | null
    if (envs && envs?.length > 0) {
      router.history.replace(
        `/project/${match.params.projectId}/environment` +
        `/${envs[0].api_key}/features`,
      )
    } else {
      router.history.replace(
        `/project/${match.params.projectId}/environment/create`,
      )
    }
    toast(
      <div>
        Removed Environment: <strong>{environment.name}</strong>
      </div>,
    )
  }

  const saveEnv = (newEnv: Partial<Environment>) => {
    // e && e.preventDefault()
    //   console.log
    const env = _.find(ProjectStore.getEnvs(), {
      api_key: match.params.environmentId,
    }) as Environment

    const { name } = env
    if (ProjectStore.isSaving || !name) {
      return
    }
    const editedEnv = { ...currentEnv, ...newEnv }
    console.log('editing', Object.assign({}, env, {
        allow_client_traits: !!currentEnv?.allow_client_traits,
        banner_colour: currentEnv?.banner_colour,
        banner_text: currentEnv?.banner_text,
        description: currentEnv?.description,
        hide_disabled_flags: currentEnv?.hide_disabled_flags,
        hide_sensitive_data: !!currentEnv?.hide_sensitive_data,
        minimum_change_request_approvals: has4EyesPermission
          ? currentEnv?.minimum_change_request_approvals
          : null,
        name: editedEnv.name || env.name,
        use_identity_composite_key_for_hashing:
          !!currentEnv?.use_identity_composite_key_for_hashing,
        use_identity_overrides_in_local_eval:
          !!currentEnv?.use_identity_overrides_in_local_eval,
        use_mv_v2_evaluation: !!currentEnv?.use_mv_v2_evaluation,
      }),)
    AppActions.editEnv(
      // Can it be a spread ?
      Object.assign({}, env, {
        allow_client_traits: !!editedEnv?.allow_client_traits,
        banner_colour: editedEnv?.banner_colour,
        banner_text: editedEnv?.banner_text,
        description: editedEnv?.description,
        hide_disabled_flags: editedEnv?.hide_disabled_flags,
        hide_sensitive_data: !!editedEnv?.hide_sensitive_data,
        minimum_change_request_approvals: has4EyesPermission
          ? editedEnv?.minimum_change_request_approvals
          : null,
        name: editedEnv.name || env.name,
        use_identity_composite_key_for_hashing:
          !!editedEnv?.use_identity_composite_key_for_hashing,
        use_identity_overrides_in_local_eval:
          !!editedEnv?.use_identity_overrides_in_local_eval,
        use_mv_v2_evaluation: !!editedEnv?.use_mv_v2_evaluation,
      }),
    )
  }

  const handleCreateWebhook = () => {
    openModal(
      'New Webhook',
      <CreateWebhookModal
        router={router}
        environmentId={match.params.environmentId}
        projectId={match.params.projectId}
        save={createWebhook}
      />,
      'side-modal',
    )
  }

  const handleEditWebhook = (webhook: WebhookType) => {
    openModal(
      'Edit Webhook',
      <CreateWebhookModal
        router={router}
        webhook={webhook}
        isEdit
        environmentId={match.params.environmentId}
        projectId={match.params.projectId}
        save={saveWebhook}
      />,
      'side-modal',
    )
  }

  const handleDeleteWebhook = (webhook: WebhookType) => {
    openModal(
      'Remove Webhook',
      <ConfirmRemoveWebhook
        environmentId={match.params.environmentId}
        projectId={match.params.projectId}
        url={webhook.url}
        cb={() => deleteWebhook(webhook)}
      />,
      'p-0',
    )
  }

  const saveDisabled = ProjectStore.isSaving || !currentEnv?.name

  const confirmToggle = (title: string, environmentProperty: string, environmentPropertyValue: boolean) => {
    openModal(
      title,
      <ConfirmToggleEnvFeature
        description={'Are you sure that you want to change this value?'}
        feature={Format.enumeration.get(environmentProperty)}
        featureValue={environmentPropertyValue}
        onToggleChange={() => {
          setCurrentEnv((currentEnvState) => {
            const newEnv = { ...currentEnvState, [environmentProperty]: environmentPropertyValue }
            console.log('newEnv', newEnv)
            // TODO: Fix env type
            saveEnv(newEnv as Environment)
            return newEnv
          })

          closeModal()
        }}
      />,
      'p-0 modal-sm',
    )
  }

  return (
    <div className='app-container container'>
      <ProjectProvider
        onRemoveEnvironment={onRemoveEnvironment}
        id={match.params.projectId}
        onRemove={onRemove}
        onSave={onSave}
      >
        {({ deleteEnv, isLoading, isSaving, project }) => {
          console.log('new', isLoading, deleteEnv)
          const env = _.find(project?.environments, {
            api_key: match.params.environmentId,
          })
          if (
            (env &&
              typeof currentEnv?.minimum_change_request_approvals ===
              'undefined') ||
            currentEnv?.api_key !== match.params.environmentId
          ) {
            // setTimeout(() => {
            //   setCurrentEnv({
            //     allow_client_traits: !!env.allow_client_traits,
            //     banner_colour: env.banner_colour || Constants.tagColors[0],
            //     banner_text: env.banner_text,
            //     hide_disabled_flags: env.hide_disabled_flags,
            //     hide_sensitive_data: !!env.hide_sensitive_data,
            //     minimum_change_request_approvals: Utils.changeRequestsEnabled(
            //       env.minimum_change_request_approvals,
            //     )
            //       ? env.minimum_change_request_approvals
            //       : null,
            //     name: env.name,
            //     use_identity_composite_key_for_hashing:
            //       !!env.use_identity_composite_key_for_hashing,
            //     use_identity_overrides_in_local_eval:
            //       !!env.use_identity_overrides_in_local_eval,
            //     use_v2_feature_versioning: !!env.use_v2_feature_versioning,
            //   })
            // }, 10)
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
                  setCurrentEnv((currentEnvState) => ({
                    ...currentEnvState,
                    enabledFeatureVersioning: true,
                  }))
                })
              },
              title: 'Enable "Feature Versioning"',
            })
          }

          return (
            <>
              {/* <EnvironmentSettingsPageTS match={this.props.match} router={this.context.router} /> */}
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
                        <form onSubmit={saveEnv}>
                          <InputGroup
                            value={currentEnv?.name || "test"}
                            inputProps={{
                              className: 'full-width',
                              name: 'env-name',
                            }}
                            className='full-width'
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>{
                              const value = Utils.safeParseEventValue(e)
                              setCurrentEnv((currentEnvState) => {
                                return {
                                  ...currentEnvState,
                                  name: value,
                                }
                              })}
                            }
                            isValid={currentEnv?.name && currentEnv?.name.length}
                            type='text'
                            title='Environment Name'
                            placeholder='Environment Name'
                          />
                          <InputGroup
                            textarea
                            // ref={(e) => (this.input = e)}
                            value={currentEnv?.description ?? ''}
                            inputProps={{
                              className: 'input--wide textarea-lg',
                            }}
                            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>{
                              const value = Utils.safeParseEventValue(e)
                              setCurrentEnv((currentEnvState) => ({
                                ...currentEnvState,
                                description: value
                              }))}
                            }
                            isValid={currentEnv?.description && currentEnv?.description.length}
                            type='text'
                            title='Environment Description'
                            placeholder='Environment Description'
                          />
                          <div className='text-right mt-5'>
                            <Button
                              id='save-env-btn'
                              type='submit'
                              disabled={saveDisabled}
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
                            setCurrentEnv((currentEnvState) => {
                              const newEnv = {
                                ...currentEnvState,
                                banner_text: value
                                  ? `${env.name} Environment`
                                  : null,
                              }
                              saveEnv(newEnv)
                              return newEnv
                            })
                          }
                          checked={typeof currentEnv?.banner_text === 'string'}
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
                        {typeof currentEnv?.banner_text === 'string' && (
                          <Row className='mt-4 flex-nowrap'>
                            <Input
                              placeholder='Banner text'
                              value={currentEnv?.banner_text}
                              onChange={(e) => {
                                setCurrentEnv((currentEnvState) => ({
                                  ...currentEnvState,
                                  banner_text: Utils.safeParseEventValue(e),
                                }))
                              }}
                              className='full-width'
                            />
                            <div className='ml-2'>
                              <ColourSelect
                                value={currentEnv?.banner_colour}
                                onChange={(banner_colour) =>
                                  setCurrentEnv((currentEnvState) => ({
                                    ...currentEnvState,
                                    banner_colour,
                                  }))
                                }
                              />
                            </div>
                            <Button onClick={saveEnv} size='small'>
                              Save
                            </Button>
                          </Row>
                        )}
                      </div>
                      {Utils.getFlagsmithHasFeature('feature_versioning') && (
                        <div>
                          <div className='col-md-8 mt-4'>
                            {currentEnv?.use_v2_feature_versioning === false && (
                              <EnvironmentVersioningListener
                                id={env.api_key}
                                versioningEnabled={currentEnv?.use_v2_feature_versioning}
                                onChange={() => {
                                  setCurrentEnv((currentEnvState) => ({
                                    ...currentEnvState,
                                    use_v2_feature_versioning: true,
                                  }))
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
                                currentEnv?.use_v2_feature_versioning ||
                                currentEnv?.enabledFeatureVersioning
                              }
                              data-test={
                                currentEnv?.use_v2_feature_versioning
                                  ? 'feature-versioning-enabled'
                                  : 'enable-versioning'
                              }
                              checked={currentEnv?.use_v2_feature_versioning}
                              onChange={onEnableVersioning}
                            />
                          </div>
                        </div>
                      )}
                      <div className='col-md-8 mt-4'>
                        <Setting
                          title='Hide sensitive data'
                          checked={currentEnv?.hide_sensitive_data}
                          onChange={(v) => {
                            console.log('v', v)
                            confirmToggle(
                              'Confirm Environment Setting',
                              'hide_sensitive_data',
                              v,
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
                      <FormGroup className='mt-4 col-md-8'>
                        <Setting
                          feature='4_EYES'
                          checked={
                            has4EyesPermission &&
                            Utils.changeRequestsEnabled(
                              currentEnv?.minimum_change_request_approvals,
                            )
                          }
                          onChange={(v) =>
                            setCurrentEnv((currentEnvState) => {
                              const newEnv = {
                                ...currentEnvState,
                                minimum_change_request_approvals: v
                                  ? 0
                                  : null,
                              }
                              saveEnv(newEnv)
                              return newEnv
                            })
                          }
                        />
                        {Utils.changeRequestsEnabled(
                          currentEnv?.minimum_change_request_approvals,
                        ) &&
                          has4EyesPermission && (
                            <div className='mt-4'>
                              <div className='mb-2'>
                                <strong>Minimum number of approvals</strong>
                              </div>
                              <Row>
                                <Flex>
                                  <Input
                                    value={`${currentEnv?.minimum_change_request_approvals}`}
                                    inputClassName='input input--wide'
                                    name='env-name'
                                    min={0}
                                    style={{ minWidth: 50 }}
                                    onChange={(e) => {
                                      if (!Utils.safeParseEventValue(e))
                                        return
                                      setCurrentEnv((currentEnvState) => ({
                                        ...currentEnvState,
                                        minimum_change_request_approvals:
                                          parseInt(
                                            Utils.safeParseEventValue(e),
                                          ),
                                      }))
                                    }}
                                    isValid={currentEnv?.minimum_change_request_approvals && currentEnv?.minimum_change_request_approvals.length}
                                    type='number'
                                    placeholder='Minimum number of approvals'
                                  />
                                </Flex>
                                <Button
                                  type='button'
                                  onClick={saveEnv}
                                  id='save-env-btn'
                                  className='ml-3'
                                  disabled={
                                    saveDisabled ||
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
                              confirmRemove(
                                _.find(project.environments, {
                                  api_key:
                                    match.params.environmentId,
                                }),
                                () => {
                                  deleteEnv(
                                    _.find(project.environments, {
                                      api_key:
                                        match.params.environmentId,
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
                        <form onSubmit={saveEnv}>
                          <div>
                            <h5 className='mb-2'>
                              Hide disabled flags from SDKs
                            </h5>
                            <Select
                              value={
                                showDisabledFlagOptions.find(
                                  (v) =>
                                    v.value ===
                                    currentEnv?.hide_disabled_flags,
                                ) || showDisabledFlagOptions[0]
                              }
                              onChange={(v) => {
                                setCurrentEnv((currentEnvState) => {
                                  const newEnv = {
                                    ...currentEnvState,
                                    hide_disabled_flags: v.value,
                                  }
                                  saveEnv(newEnv)
                                  return newEnv
                                })
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
                                to={`/project/${match.params.projectId}/settings`}
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
                              checked={currentEnv?.allow_client_traits}
                              onChange={(v) => {
                                setCurrentEnv((currentEnvState) => {
                                  const newEnv = {
                                    ...currentEnvState,
                                    allow_client_traits: v,
                                  }
                                  saveEnv(newEnv)
                                  return newEnv
                                })
                              }}
                            />
                          </div>
                          <div className='mt-4'>
                            <Setting
                              checked={currentEnv?.use_identity_composite_key_for_hashing}
                              onChange={(v) => {
                                setCurrentEnv((currentEnvState) => {
                                  const newEnv = {
                                    ...currentEnvState,
                                    use_identity_composite_key_for_hashing: v,
                                  }
                                  saveEnv(newEnv)
                                  return newEnv
                                })
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
                          {Utils.getFlagsmithHasFeature(
                            'use_identity_overrides_in_local_eval',
                          ) && (
                              <div className='mt-4'>
                                <Setting
                                  title='Use identity overrides in local evaluation'
                                  description={`This determines whether server-side SDKs running in local evaluation mode receive identity overrides in the environment document.`}
                                  checked={!!currentEnv?.use_identity_overrides_in_local_eval}
                                  onChange={(v) => {
                                    console.log('identity', v)
                                    setCurrentEnv((currentEnvState) => {
                                      const newEnv = {
                                        ...currentEnvState,
                                        use_identity_overrides_in_local_eval: v,
                                      }
                                      console.log(newEnv)
                                      saveEnv(newEnv)
                                      return newEnv
                                    })
                                  }}
                                />
                              </div>
                            )}
                        </form>
                      </div>
                    </div>
                  </TabItem>
                  <TabItem tabLabel='Permissions'>
                    <FormGroup>
                      <EditPermissions
                        tabClassName='flat-panel'
                        parentId={match.params.projectId}
                        parentLevel='project'
                        parentSettingsLink={`/project/${match.params.projectId}/settings`}
                        id={match.params.environmentId}
                        envId={env.id}
                        router={router}
                        level='environment'
                        roleTabTitle='Environment Permissions'
                        roles={roles}
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
                      <Button onClick={handleCreateWebhook}>
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
                                handleEditWebhook(webhook)
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
                                    handleDeleteWebhook(webhook)
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
                          isLoading={webhooksLoading}
                        />
                      )}
                    </FormGroup>
                  </TabItem>
                  {metadataEnable &&
                    environmentContentType?.id && (
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
                                projectId={match.params.projectId}
                                entityId={currentEnv?.api_key || ''}
                                envName={currentEnv?.name}
                                entityContentType={
                                  environmentContentType?.id
                                }
                                entity={
                                  environmentContentType.model
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



EnvironmentSettingsPageTS.displayName = 'EnvironmentSettingsPage'

export default ConfigProvider(withWebhooks(EnvironmentSettingsPageTS))
