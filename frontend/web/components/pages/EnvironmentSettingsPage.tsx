import React, { useCallback, useEffect, useMemo, useState } from 'react'
import ConfirmRemoveEnvironment from 'components/modals/ConfirmRemoveEnvironment'
import ProjectStore from 'common/stores/project-store'
import ConfigProvider from 'common/providers/ConfigProvider'
import CreateWebhookModal from 'components/modals/CreateWebhook'
import ConfirmRemoveWebhook from 'components/modals/ConfirmRemoveWebhook'
import ConfirmToggleEnvFeature from 'components/modals/ConfirmToggleEnvFeature'
import EditPermissions from 'components/EditPermissions'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
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
import { Link, useHistory, useRouteMatch } from 'react-router-dom'
import { enableFeatureVersioning } from 'common/services/useEnableFeatureVersioning'
import AddMetadataToEntity from 'components/metadata/AddMetadataToEntity'
import { getSupportedContentType } from 'common/services/useSupportedContentType'
import Format from 'common/utils/format'
import Setting from 'components/Setting'
import API from 'project/api'
import AppActions from 'common/dispatcher/app-actions'
import {
  Environment,
  Webhook,
  Role,
  RolePermission,
} from 'common/types/responses'
import PanelSearch from 'components/PanelSearch'
import moment from 'moment'
import Panel from 'components/base/grid/Panel'
import ProjectProvider from 'common/providers/ProjectProvider'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import useFormNotSavedModal from 'components/hooks/useFormNotSavedModal'
import {
  useCreateWebhookMutation,
  useDeleteWebhookMutation,
  useGetWebhooksQuery,
  useUpdateWebhookMutation,
} from 'common/services/useWebhooks'
import Button from 'components/base/forms/Button'
import Input from 'components/base/forms/Input'
import { useGetEnvironmentQuery } from 'common/services/useEnvironment'
import { useRouteContext } from 'components/providers/RouteContext'
import SettingTitle from 'components/SettingTitle'
import ChangeRequestsSetting from 'components/ChangeRequestsSetting'

const showDisabledFlagOptions: { label: string; value: boolean | null }[] = [
  { label: 'Inherit from Project', value: null },
  { label: 'Disabled', value: false },
  { label: 'Enabled', value: true },
]

const EnvironmentSettingsPage: React.FC = () => {
  const [createWebhook] = useCreateWebhookMutation()
  const [deleteWebhook] = useDeleteWebhookMutation()
  const [saveWebhook] = useUpdateWebhookMutation()

  const store = getStore()
  const history = useHistory()
  const match = useRouteMatch<{
    projectId: string
    environmentId: string
  }>()
  const { projectId } = useRouteContext()
  const [currentEnv, setCurrentEnv] = useState<Environment | null>(null)
  const [roles, setRoles] = useState<Role[]>([])
  const [environmentContentType, setEnvironmentContentType] =
    useState<any>(null)

  const env = useMemo(() => {
    return (
      (ProjectStore?.getEnvs() as Environment[] | null | undefined)?.find(
        (env: Environment) => env.api_key === match.params.environmentId,
      ) ?? null
    )
  }, [match.params.environmentId])

  const { data: webhooks, isLoading: webhooksLoading } = useGetWebhooksQuery(
    { environmentId: match.params.environmentId },
    { skip: !match.params.environmentId },
  )

  const onDiscard = () => {
    if (env && currentEnv) {
      setCurrentEnv({
        ...currentEnv,
        banner_colour: env.banner_colour,
        banner_text: env.banner_text,
        description: env.description,
        name: env.name,
      })
    }
  }

  const [DirtyFormModal, setIsDirty, isDirty] = useFormNotSavedModal({
    onDiscard: onDiscard,
  })

  const {
    data: environmentData,
    isFetching: isFetchingEnvironment,
    isSuccess: isSuccessEnvironment,
  } = useGetEnvironmentQuery(
    { id: env?.api_key ?? '' },
    {
      pollingInterval: currentEnv?.use_v2_feature_versioning ? undefined : 2000,
      skip: isDirty || currentEnv?.use_v2_feature_versioning || !env?.api_key,
    },
  )

  const has4EyesPermission = Utils.getPlansPermission('4_EYES')
  const metadataEnable = Utils.getPlansPermission('METADATA')

  const getEnvironment = useCallback(async () => {
    if (!env) return

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

    const matchingItems: Role[] = roles.data.results.filter((item1: Role) =>
      roleEnvironmentPermissions.data.results.some(
        (item2: RolePermission) => item2.role === item1.id,
      ),
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
  }, [store, env])

  useEffect(() => {
    AppActions.getProject(projectId)
  }, [projectId])

  useEffect(() => {
    getEnvironment()
  }, [match.params.environmentId, getEnvironment])

  useEffect(() => {
    API.trackPage(Constants.pages.ENVIRONMENT_SETTINGS)
    getEnvironment()
  }, [getEnvironment])

  // This watches exclusively the update of use_v2_feature_versioning that is done async
  useEffect(() => {
    if (isFetchingEnvironment || !env?.id) {
      return
    }

    const isEnvDataVersioningEnabled =
      environmentData?.use_v2_feature_versioning
    const isCurrentEnvVersioningDisabled =
      !!currentEnv && !currentEnv?.use_v2_feature_versioning
    if (isEnvDataVersioningEnabled && isCurrentEnvVersioningDisabled) {
      setCurrentEnv((currentEnvState) => {
        AppActions.editEnv(environmentData)
        return {
          ...currentEnvState,
          ...environmentData,
          use_v2_feature_versioning: environmentData?.use_v2_feature_versioning,
        }
      })
    }
  }, [
    env?.id,
    isFetchingEnvironment,
    environmentData,
    isSuccessEnvironment,
    currentEnv,
    currentEnv?.use_v2_feature_versioning,
  ])

  const onSave = () => {
    toast('Environment Saved')
  }

  const onRemove = () => {
    toast('Your project has been removed')
    history.replace(Utils.getOrganisationHomePage())
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
      history.replace(
        `/project/${projectId}/environment` + `/${envs[0].api_key}/features`,
      )
    } else {
      history.replace(`/project/${projectId}/environment/create`)
    }
    toast(
      <div>
        Removed Environment: <strong>{environment.name}</strong>
      </div>,
    )
  }

  const updateCurrentEnv = (
    newEnv: Partial<Environment> = {},
    shouldSaveUpdate?: boolean,
    isDirtyDisabled?: boolean,
  ) => {
    if (!isDirtyDisabled) {
      setIsDirty(true)
    }
    setCurrentEnv((currentEnvState) => {
      if (!currentEnvState) return null
      const newEnvState = {
        ...currentEnvState,
        ...newEnv,
      }
      if (shouldSaveUpdate) {
        saveEnv(newEnvState)
      }
      return newEnvState
    })
  }

  const saveEnv = (newEnv: Partial<Environment> = {}) => {
    if (ProjectStore.isSaving || !currentEnv?.name) {
      return
    }
    const editedEnv = { ...currentEnv, ...newEnv }

    AppActions.editEnv(
      Object.assign({}, currentEnv, {
        allow_client_traits: !!editedEnv?.allow_client_traits,
        banner_colour: editedEnv?.banner_colour,
        banner_text: editedEnv?.banner_text,
        description: editedEnv?.description,
        hide_disabled_flags: editedEnv?.hide_disabled_flags,
        hide_sensitive_data: !!editedEnv?.hide_sensitive_data,
        minimum_change_request_approvals: has4EyesPermission
          ? editedEnv?.minimum_change_request_approvals
          : null,
        name: editedEnv.name || currentEnv.name,
        use_identity_composite_key_for_hashing:
          !!editedEnv?.use_identity_composite_key_for_hashing,
        use_identity_overrides_in_local_eval:
          !!editedEnv?.use_identity_overrides_in_local_eval,
        use_mv_v2_evaluation: !!editedEnv?.use_mv_v2_evaluation,
      }),
    )
    setIsDirty(false)
  }

  const handleCreateWebhook = () => {
    openModal(
      'New Webhook',
      <CreateWebhookModal
        environmentId={match.params.environmentId}
        projectId={projectId}
        save={(webhook: Webhook) =>
          createWebhook({
            ...webhook,
            environmentId: match.params.environmentId,
          })
        }
      />,
      'side-modal',
    )
  }

  const handleEditWebhook = (webhook: Webhook) => {
    openModal(
      'Edit Webhook',
      <CreateWebhookModal
        webhook={webhook}
        isEdit
        environmentId={match.params.environmentId}
        projectId={projectId}
        save={(webhook: Webhook) =>
          saveWebhook({ ...webhook, environmentId: match.params.environmentId })
        }
      />,
      'side-modal',
    )
  }

  const handleDeleteWebhook = (webhook: Webhook) => {
    openModal(
      'Remove Webhook',
      <ConfirmRemoveWebhook
        environmentId={match.params.environmentId}
        projectId={projectId}
        url={webhook.url}
        cb={() =>
          deleteWebhook({
            environmentId: match.params.environmentId,
            id: webhook.id,
          })
        }
      />,
      'p-0',
    )
  }

  const saveDisabled = ProjectStore.isSaving || !currentEnv?.name

  const confirmToggle = (
    title: string,
    environmentProperty: string,
    environmentPropertyValue: boolean,
  ) => {
    openModal(
      title,
      <ConfirmToggleEnvFeature
        description={'Are you sure that you want to change this value?'}
        feature={Format.enumeration.get(environmentProperty)}
        featureValue={environmentPropertyValue}
        onToggleChange={() => {
          updateCurrentEnv(
            { [environmentProperty]: environmentPropertyValue },
            true,
          )
          closeModal()
        }}
      />,
      'p-0 modal-sm',
    )
  }

  const onEnableVersioning = () => {
    if (!currentEnv?.api_key) return
    openConfirm({
      body: 'This will allow you to attach versions to updating feature values and segment overrides. Note: this may take several minutes to process',
      onYes: () => {
        enableFeatureVersioning(store, {
          environmentId: currentEnv?.api_key,
        }).then(() => {
          toast(
            'Feature Versioning Enabled, this may take several minutes to process.',
          )
          updateCurrentEnv(
            {
              enabledFeatureVersioning: true,
            },
            false,
            true,
          )
        })
      },
      title: 'Enable "Feature Versioning"',
    })
  }

  return (
    <div className='app-container container'>
      <ProjectProvider
        onRemoveEnvironment={onRemoveEnvironment}
        id={projectId}
        onRemove={onRemove}
        onSave={onSave}
      >
        {({ deleteEnv, isLoading, isSaving, project }) => {
          const env = _.find(project?.environments, {
            api_key: match.params.environmentId,
          })
          if (
            (env &&
              typeof env?.minimum_change_request_approvals === 'undefined') ||
            env?.api_key !== match.params.environmentId
          ) {
            setTimeout(() => {
              const minimumChangeRequestApprovals = Utils.changeRequestsEnabled(
                env?.minimum_change_request_approvals,
              )
              updateCurrentEnv(
                {
                  allow_client_traits: !!env?.allow_client_traits,
                  banner_colour: env?.banner_colour || Constants.tagColors[0],
                  banner_text: env?.banner_text,
                  hide_disabled_flags: env?.hide_disabled_flags || false,
                  hide_sensitive_data: !!env?.hide_sensitive_data,
                  minimum_change_request_approvals:
                    minimumChangeRequestApprovals
                      ? env?.minimum_change_request_approvals
                      : null,
                  name: env?.name ?? '',
                  use_identity_composite_key_for_hashing:
                    !!env?.use_identity_composite_key_for_hashing,
                  use_identity_overrides_in_local_eval:
                    !!env?.use_identity_overrides_in_local_eval,
                  use_v2_feature_versioning: !!env?.use_v2_feature_versioning,
                },
                false,
                true,
              )
            }, 10)
          }

          return (
            <>
              <DirtyFormModal />
              <PageTitle title='Environment Settings' />
              {isLoading && (
                <div className='centered-container'>
                  <Loader />
                </div>
              )}
              {!isLoading && (
                <Tabs urlParam='tab' className='mt-0' uncontrolled noFocus>
                  <TabItem tabLabel='General'>
                    <div className='mt-4 col-md-8'>
                      <SettingTitle>Environment Information</SettingTitle>
                      <JSONReference title={'Environment'} json={env} />
                      <form
                        onSubmit={(e) => {
                          e.preventDefault()
                          saveEnv()
                        }}
                      >
                        <InputGroup
                          value={currentEnv?.name}
                          inputProps={{
                            className: 'full-width',
                            name: 'env-name',
                          }}
                          className='full-width'
                          onChange={(
                            e: React.ChangeEvent<HTMLInputElement>,
                          ) => {
                            const value = Utils.safeParseEventValue(e)
                            updateCurrentEnv({ name: value }, false)
                          }}
                          isValid={currentEnv?.name && currentEnv?.name.length}
                          type='text'
                          title='Name'
                          placeholder='Environment Name'
                        />
                        <InputGroup
                          textarea
                          // ref={(e) => (this.input = e)}
                          value={currentEnv?.description ?? ''}
                          inputProps={{
                            className: 'input--wide textarea-lg',
                          }}
                          onChange={(
                            e: React.ChangeEvent<HTMLInputElement>,
                          ) => {
                            const value = Utils.safeParseEventValue(e)
                            updateCurrentEnv({ description: value })
                          }}
                          isValid={
                            currentEnv?.description &&
                            currentEnv?.description.length
                          }
                          type='text'
                          title='Description'
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
                      <SettingTitle>Additional Settings</SettingTitle>
                      <div className='mt-4'>
                        <Setting
                          onChange={(value) =>
                            updateCurrentEnv(
                              {
                                banner_text: value
                                  ? `${currentEnv?.name} Environment`
                                  : null,
                              },
                              true,
                            )
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
                              onChange={(
                                e: React.ChangeEvent<HTMLInputElement>,
                              ) => {
                                const bannerText = Utils.safeParseEventValue(e)
                                updateCurrentEnv(
                                  { banner_text: bannerText },
                                  false,
                                )
                              }}
                              className='full-width'
                            />
                            <div className='ml-2'>
                              <ColourSelect
                                value={currentEnv?.banner_colour || ''}
                                onChange={(banner_colour) =>
                                  updateCurrentEnv({ banner_colour }, false)
                                }
                              />
                            </div>
                            <Button onClick={() => saveEnv()} size='small'>
                              Save
                            </Button>
                          </Row>
                        )}
                      </div>
                      {Utils.getFlagsmithHasFeature('feature_versioning') && (
                        <div>
                          <div className='mt-4'>
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
                      <FormGroup className='mt-4'>
                        <ChangeRequestsSetting
                          feature='4_EYES'
                          isLoading={saveDisabled}
                          value={currentEnv?.minimum_change_request_approvals}
                          onSave={saveEnv}
                          onToggle={(v) =>
                            updateCurrentEnv(
                              {
                                minimum_change_request_approvals: v,
                              },
                              true,
                            )
                          }
                          onChange={(value) => {
                            updateCurrentEnv({
                              minimum_change_request_approvals: value
                                ? parseInt(value)
                                : undefined,
                            })
                          }}
                        />
                      </FormGroup>
                      <SettingTitle danger>Delete Environment</SettingTitle>
                      <FormGroup className='mt-4'>
                        <Row space>
                          <p className='fs-small lh-sm mb-0'>
                            This environment will be permanently deleted.
                          </p>
                          <Button
                            id='delete-env-btn'
                            onClick={() => {
                              const envToRemove = _.find(
                                project?.environments,
                                {
                                  api_key: match.params.environmentId,
                                },
                              )
                              if (!envToRemove) return
                              confirmRemove(envToRemove, () => {
                                deleteEnv(envToRemove)
                              })
                            }}
                            theme='danger'
                          >
                            Delete Environment
                          </Button>
                        </Row>
                      </FormGroup>
                    </div>
                  </TabItem>
                  <TabItem data-test='js-sdk-settings' tabLabel='SDK Settings'>
                    <div className='mt-4'>
                      <JSONReference
                        title={'Environment'}
                        json={env}
                        className='mb-4'
                      />
                      <form onSubmit={() => saveEnv()}>
                        <div>
                          <h5 className='mb-2'>
                            Hide disabled flags from SDKs
                          </h5>
                          <Select
                            value={
                              showDisabledFlagOptions.find(
                                (option) =>
                                  option.value ===
                                  currentEnv?.hide_disabled_flags,
                              ) || showDisabledFlagOptions[0]
                            }
                            onChange={(option: {
                              label: string
                              value: boolean | null
                            }) => {
                              updateCurrentEnv(
                                { hide_disabled_flags: option.value },
                                true,
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
                            enabling this will prevent the API from returning
                            features that are disabled. You can also manage this
                            in{' '}
                            <Link to={`/project/${projectId}/settings`}>
                              Project settings
                            </Link>
                            .
                          </p>
                        </div>
                        <div className='mt-4'>
                          <Setting
                            title='Persist traits when using client-side SDK keys'
                            description={
                              'If enabled, Flagsmith will persist any non-transient traits sent by SDKs using client-side keys when remotely evaluating flags.'
                            }
                            checked={currentEnv?.allow_client_traits}
                            onChange={(value) => {
                              updateCurrentEnv(
                                { allow_client_traits: value },
                                true,
                              )
                            }}
                          />
                        </div>
                        <div className='mt-4'>
                          <Setting
                            checked={
                              currentEnv?.use_identity_composite_key_for_hashing
                            }
                            onChange={(value) =>
                              updateCurrentEnv(
                                {
                                  use_identity_composite_key_for_hashing: value,
                                },
                                true,
                              )
                            }
                            title={`Use consistent hashing`}
                            description={
                              <div>
                                Enabling this setting will ensure that
                                multivariate and percentage split evaluations
                                made by the API are consistent with those made
                                by local evaluation mode in our server side
                                SDKs.
                                <div className='text-danger'>
                                  Toggling this setting will mean that some
                                  users will start receiving different values
                                  for multivariate flags and flags with a
                                  percentage split segment override via the API
                                  / remote evaluation. Values received in local
                                  evaluation mode will not change.
                                </div>
                              </div>
                            }
                          />
                          <Setting
                            title='Hide sensitive data'
                            checked={currentEnv?.hide_sensitive_data}
                            onChange={(value) => {
                              confirmToggle(
                                'Confirm Environment Setting',
                                'hide_sensitive_data',
                                value,
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
                        {Utils.getFlagsmithHasFeature(
                          'use_identity_overrides_in_local_eval',
                        ) && (
                          <div className='mt-4'>
                            <Setting
                              title='Use identity overrides in local evaluation'
                              description={`This determines whether server-side SDKs running in local evaluation mode receive identity overrides in the environment document.`}
                              checked={
                                !!currentEnv?.use_identity_overrides_in_local_eval
                              }
                              onChange={(value) => {
                                updateCurrentEnv(
                                  {
                                    use_identity_overrides_in_local_eval: value,
                                  },
                                  true,
                                )
                              }}
                            />
                          </div>
                        )}
                      </form>
                    </div>
                  </TabItem>
                  <TabItem tabLabel='Permissions'>
                    <FormGroup>
                      <EditPermissions
                        tabClassName='flat-panel'
                        parentId={projectId}
                        parentLevel='project'
                        parentSettingsLink={`/project/${projectId}/settings`}
                        id={match.params.environmentId}
                        envId={env?.id}
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
                          changed. You can configure 1 or more Feature Webhooks
                          per Environment.{' '}
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
                  {metadataEnable && environmentContentType?.id && (
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
                              organisationId={AccountStore.getOrganisation().id}
                              projectId={projectId}
                              entityId={currentEnv?.api_key ?? ''}
                              envName={currentEnv?.name}
                              entityContentType={environmentContentType?.id}
                              entity={environmentContentType.model}
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

EnvironmentSettingsPage.displayName = 'EnvironmentSettingsPage'

export default ConfigProvider(EnvironmentSettingsPage)
