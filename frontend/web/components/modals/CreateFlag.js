import React, { Component } from 'react'
import withSegmentOverrides from 'common/providers/withSegmentOverrides'
import Constants from 'common/constants'
import data from 'common/data/base/_data'
import ProjectStore from 'common/stores/project-store'
import ConfigProvider from 'common/providers/ConfigProvider'
import FeatureListStore from 'common/stores/feature-list-store'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip as RechartsTooltip,
  XAxis,
  YAxis,
} from 'recharts'
import Tabs from 'components/base/forms/Tabs'
import TabItem from 'components/base/forms/TabItem'
import SegmentOverrides from 'components/SegmentOverrides'
import AddEditTags from 'components/tags/AddEditTags'
import FlagOwners from 'components/FlagOwners'
import ChangeRequestModal from './ChangeRequestModal'
import Feature from 'components/Feature'
import classNames from 'classnames'
import InfoMessage from 'components/InfoMessage'
import JSONReference from 'components/JSONReference'
import ErrorMessage from 'components/ErrorMessage'
import Permission from 'common/providers/Permission'
import IdentitySelect from 'components/IdentitySelect'
import { setInterceptClose, setModalTitle } from './base/ModalDefault'
import Icon from 'components/Icon'
import ModalHR from './ModalHR'
import FeatureValue from 'components/FeatureValue'
import { getStore } from 'common/store'
import FlagOwnerGroups from 'components/FlagOwnerGroups'
import ExistingChangeRequestAlert from 'components/ExistingChangeRequestAlert'
import Button from 'components/base/forms/Button'
import AddMetadataToEntity from 'components/metadata/AddMetadataToEntity'
import { getSupportedContentType } from 'common/services/useSupportedContentType'
import { getGithubIntegration } from 'common/services/useGithubIntegration'
import { createExternalResource } from 'common/services/useExternalResource'
import { removeUserOverride } from 'components/RemoveUserOverride'
import MyIssueSelect from 'components/MyIssuesSelect'
import MyPullRequestsSelect from 'components/MyPullRequestsSelect'
import MyRepositoriesSelect from 'components/MyRepositoriesSelect'
import ExternalResourcesTable from 'components/ExternalResourcesTable'

const CreateFlag = class extends Component {
  static displayName = 'CreateFlag'

  constructor(props, context) {
    super(props, context)
    const {
      description,
      enabled,
      feature_state_value,
      is_archived,
      is_server_key_only,
      metadata,
      multivariate_options,
      name,
      tags,
    } = this.props.projectFlag
      ? Utils.getFlagValue(
          this.props.projectFlag,
          this.props.environmentFlag,
          this.props.identityFlag,
        )
      : {
          multivariate_options: [],
        }
    const { allowEditDescription } = this.props
    if (this.props.projectFlag) {
      this.userOverridesPage(1)
    }
    this.state = {
      allowEditDescription,
      default_enabled: enabled,
      description,
      enabledIndentity: false,
      enabledSegment: false,
      environmentFlag: this.props.environmentFlag,
      externalResource: {},
      externalResources: [],
      featureContentType: {},
      githubId: '',
      hasIntegrationWithGithub: false,
      hasMetadataRequired: false,
      identityVariations:
        this.props.identityFlag &&
        this.props.identityFlag.multivariate_feature_state_values
          ? _.cloneDeep(
              this.props.identityFlag.multivariate_feature_state_values,
            )
          : [],
      initial_value:
        typeof feature_state_value === 'undefined'
          ? undefined
          : Utils.getTypedValue(feature_state_value),
      isEdit: !!this.props.projectFlag,
      is_archived,
      is_server_key_only,
      metadata: [],
      multivariate_options: _.cloneDeep(multivariate_options),
      name,
      period: 30,
      repoName: '',
      repoOwner: '',
      selectedIdentity: null,
      tags: tags || [],
    }
  }

  getState = () => {}

  close() {
    closeModal()
  }

  componentDidUpdate(prevProps) {
    ES6Component(this)
    if (
      !this.props.identity &&
      this.props.environmentVariations !== prevProps.environmentVariations
    ) {
      if (
        this.props.environmentVariations &&
        this.props.environmentVariations.length
      ) {
        this.setState({
          multivariate_options:
            this.state.multivariate_options &&
            this.state.multivariate_options.map((v) => {
              const matchingVariation = (
                this.props.multivariate_options ||
                this.props.environmentVariations
              ).find((e) => e.multivariate_feature_option === v.id)
              return {
                ...v,
                default_percentage_allocation:
                  (matchingVariation &&
                    matchingVariation.percentage_allocation) ||
                  v.default_percentage_allocation ||
                  0,
              }
            }),
        })
      }
    }
  }

  onClosing = () => {
    if (this.state.isEdit) {
      return new Promise((resolve) => {
        if (
          this.state.valueChanged ||
          this.state.segmentsChanged ||
          this.state.settingsChanged
        ) {
          openConfirm({
            body: 'Closing this will discard your unsaved changes.',
            noText: 'Cancel',
            onNo: () => resolve(false),
            onYes: () => resolve(true),
            title: 'Discard changes',
            yesText: 'Ok',
          })
        } else {
          resolve(true)
        }
      })
    }
    return Promise.resolve(true)
  }

  componentDidMount = () => {
    setInterceptClose(this.onClosing)
    if (!this.state.isEdit && !E2E) {
      this.focusTimeout = setTimeout(() => {
        this.input.focus()
        this.focusTimeout = null
      }, 500)
    }
    if (
      !Project.disableAnalytics &&
      this.props.projectFlag &&
      this.state.environmentFlag
    ) {
      this.getFeatureUsage()
    }
    if (Utils.getFlagsmithHasFeature('enable_metadata')) {
      getSupportedContentType(getStore(), {
        organisation_id: AccountStore.getOrganisation().id,
      }).then((res) => {
        const featureContentType = Utils.getContentType(
          res.data,
          'model',
          'feature',
        )
        this.setState({ featureContentType: featureContentType })
      })
    }

    if (Utils.getFlagsmithHasFeature('github_integration')) {
      getGithubIntegration(getStore(), {
        organisation_id: AccountStore.getOrganisation().id,
      }).then((res) => {
        this.setState({
          githubId: res?.data?.results[0]?.id,
          hasIntegrationWithGithub: !!res?.data?.results?.length,
        })
      })
    }
  }

  componentWillUnmount() {
    if (this.focusTimeout) {
      clearTimeout(this.focusTimeout)
    }
  }

  userOverridesPage = (page) => {
    if (Utils.getIsEdge()) {
      if (!Utils.getShouldHideIdentityOverridesTab(ProjectStore.model)) {
        data
          .get(
            `${Project.api}environments/${this.props.environmentId}/edge-identity-overrides?feature=${this.props.projectFlag.id}&page=${page}`,
          )
          .then((userOverrides) => {
            this.setState({
              userOverrides: userOverrides.results.map((v) => ({
                ...v.feature_state,
                identity: {
                  id: v.identity_uuid,
                  identifier: v.identifier,
                },
              })),
              userOverridesPaging: {
                count: userOverrides.count,
                currentPage: page,
                next: userOverrides.next,
              },
            })
          })
      }

      return
    }
    data
      .get(
        `${Project.api}environments/${
          this.props.environmentId
        }/${Utils.getFeatureStatesEndpoint()}/?anyIdentity=1&feature=${
          this.props.projectFlag.id
        }&page=${page}`,
      )
      .then((userOverrides) => {
        this.setState({
          userOverrides: userOverrides.results,
          userOverridesPaging: {
            count: userOverrides.count,
            currentPage: page,
            next: userOverrides.next,
          },
        })
      })
  }

  getFeatureUsage = () => {
    if (this.state.environmentFlag) {
      AppActions.getFeatureUsage(
        this.props.projectId,
        this.state.environmentFlag.environment,
        this.props.projectFlag.id,
        this.state.period,
      )
    }
  }
  save = (func, isSaving) => {
    const {
      environmentId,
      identity,
      identityFlag,
      projectFlag: _projectFlag,
      segmentOverrides,
    } = this.props
    const {
      default_enabled,
      description,
      environmentFlag,
      initial_value,
      is_archived,
      is_server_key_only,
      name,
    } = this.state
    const projectFlag = {
      skipSaveProjectFeature: this.state.skipSaveProjectFeature,
      ..._projectFlag,
    }
    const hasMultivariate =
      this.state.environmentFlag &&
      this.state.environmentFlag.multivariate_feature_state_values &&
      this.state.environmentFlag.multivariate_feature_state_values.length
    if (identity) {
      !isSaving &&
        name &&
        func({
          environmentFlag,
          environmentId,
          identity,
          identityFlag: Object.assign({}, identityFlag || {}, {
            enabled: default_enabled,
            feature_state_value: hasMultivariate
              ? this.state.environmentFlag.feature_state_value
              : initial_value,
            multivariate_options: this.state.identityVariations,
          }),
          projectFlag,
        })
    } else {
      FeatureListStore.isSaving = true
      FeatureListStore.trigger('change')
      !isSaving &&
        name &&
        func(
          this.props.projectId,
          this.props.environmentId,
          {
            default_enabled,
            description,
            initial_value,
            is_archived,
            is_server_key_only,
            metadata:
              !this.props.projectFlag?.metadata ||
              (this.props.projectFlag.metadata !== this.state.metadata &&
                this.state.metadata.length)
                ? this.state.metadata
                : this.props.projectFlag.metadata,
            multivariate_options: this.state.multivariate_options,
            name,
            tags: this.state.tags,
          },
          projectFlag,
          environmentFlag,
          segmentOverrides,
        )
    }
  }

  changeSegment = (items) => {
    const { enabledSegment } = this.state
    items.forEach((item) => {
      item.enabled = enabledSegment
    })
    this.props.updateSegments(items)
    this.setState({ enabledSegment: !enabledSegment })
  }

  changeIdentity = (items) => {
    const { environmentId } = this.props
    const { enabledIndentity } = this.state

    Promise.all(
      items.map(
        (item) =>
          new Promise((resolve) => {
            AppActions.changeUserFlag({
              environmentId,
              identity: item.identity.id,
              identityFlag: item.id,
              onSuccess: resolve,
              payload: {
                enabled: enabledIndentity,
                id: item.identity.id,
                value: item.identity.identifier,
              },
            })
          }),
      ),
    ).then(() => {
      this.userOverridesPage(1)
    })

    this.setState({ enabledIndentity: !enabledIndentity })
  }

  toggleUserFlag = ({ enabled, id, identity }) => {
    const { environmentId } = this.props

    AppActions.changeUserFlag({
      environmentId,
      identity: identity.id,
      identityFlag: id,
      onSuccess: () => {
        this.userOverridesPage(1)
      },
      payload: {
        enabled: !enabled,
        id: identity.id,
        value: identity.identifier,
      },
    })
  }

  drawChart = (data) => {
    return data?.length ? (
      <ResponsiveContainer height={400} width='100%' className='mt-4'>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray='3 5' strokeOpacity={0.4} />
          <XAxis
            padding='gap'
            interval={0}
            height={100}
            angle={-90}
            textAnchor='end'
            allowDataOverflow={false}
            dataKey='day'
            tick={{ dx: -4, fill: '#656D7B' }}
            tickLine={false}
            axisLine={{ stroke: '#656D7B' }}
          />
          <YAxis
            allowDataOverflow={false}
            tick={{ fill: '#656D7B' }}
            axisLine={{ stroke: '#656D7B' }}
          />
          <RechartsTooltip cursor={{ fill: 'transparent' }} />
          <Bar
            dataKey={'count'}
            stackId='a'
            fill='rgba(149, 108, 255,0.48)'
            barSize={14}
          />
        </BarChart>
      </ResponsiveContainer>
    ) : (
      <div className='modal-caption fs-small lh-sm'>
        There has been no activity for this flag within the past month. Find out
        about Flag Analytics{' '}
        <Button
          theme='text'
          target='_blank'
          href='https://docs.flagsmith.com/advanced-use/flag-analytics'
          className='fw-normal'
        >
          here
        </Button>
        .
      </div>
    )
  }

  addItem = () => {
    const { environmentId, identity, projectFlag } = this.props
    const { environmentFlag } = this.state
    this.setState({ isLoading: true })
    const selectedIdentity = this.state.selectedIdentity.value
    const identities = identity ? identity.identifier : []

    if (!_.find(identities, (v) => v.identifier === selectedIdentity)) {
      data
        .post(
          `${
            Project.api
          }environments/${environmentId}/${Utils.getIdentitiesEndpoint()}/${selectedIdentity}/${Utils.getFeatureStatesEndpoint()}/`,
          {
            enabled: !environmentFlag.enabled,
            feature: projectFlag.id,
            feature_state_value: environmentFlag.value || null,
          },
        )
        .then(() => {
          this.setState({
            isLoading: false,
            selectedIdentity: null,
          })
          this.userOverridesPage(1)
        })
        .catch((e) => {
          this.setState({ error: e, isLoading: false })
        })
    } else {
      this.setState({
        isLoading: false,
        selectedIdentity: null,
      })
    }
  }

  addVariation = () => {
    this.setState({
      multivariate_options: this.state.multivariate_options.concat([
        {
          ...Utils.valueToFeatureState(''),
          default_percentage_allocation: 0,
        },
      ]),
      valueChanged: true,
    })
  }

  removeVariation = (i) => {
    this.state.valueChanged = true
    if (this.state.multivariate_options[i].id) {
      const idToRemove = this.state.multivariate_options[i].id
      if (idToRemove) {
        this.props.removeMultivariateOption(idToRemove)
      }
      this.state.multivariate_options.splice(i, 1)
      this.forceUpdate()
    } else {
      this.state.multivariate_options.splice(i, 1)
      this.forceUpdate()
    }
  }

  updateVariation = (i, e, environmentVariations) => {
    this.props.onEnvironmentVariationsChange(environmentVariations)
    this.state.multivariate_options[i] = e
    this.state.valueChanged = true
    this.forceUpdate()
  }

  render() {
    const {
      default_enabled,
      description,
      enabledIndentity,
      enabledSegment,
      externalResourceType,
      featureContentType,
      featureExternalResource,
      githubId,
      hasIntegrationWithGithub,
      initial_value,
      isEdit,
      multivariate_options,
      name,
      repoName,
      repoOwner,
      status,
    } = this.state
    const FEATURE_ID_MAXLENGTH = Constants.forms.maxLength.FEATURE_ID

    const { identity, identityName, projectFlag } = this.props
    const Provider = identity ? IdentityProvider : FeatureListProvider
    const environmentVariations = this.props.environmentVariations
    const environment = ProjectStore.getEnvironment(this.props.environmentId)
    const isVersioned = !!environment?.use_v2_feature_versioning
    const is4Eyes =
      !!environment &&
      Utils.changeRequestsEnabled(environment.minimum_change_request_approvals)
    const canSchedule = Utils.getPlansPermission('SCHEDULE_FLAGS')
    const project = ProjectStore.model
    const caseSensitive = project?.only_allow_lower_case_feature_names
    const regex = project?.feature_name_regex
    const controlValue = Utils.calculateControl(multivariate_options)
    const invalid =
      !!multivariate_options && multivariate_options.length && controlValue < 0
    const existingChangeRequest = this.props.changeRequest
    const hideIdentityOverridesTab = Utils.getShouldHideIdentityOverridesTab()
    const noPermissions = this.props.noPermissions
    const _createExternalResourse = () => {
      createExternalResource(getStore(), {
        body: {
          feature: projectFlag.id,
          metadata: { status: status },
          type:
            externalResourceType === 'Github Issue'
              ? 'GITHUB_ISSUE'
              : 'GITHUB_PR',
          url: featureExternalResource,
        },
        feature_id: projectFlag.id,
        project_id: `${this.props.projectId}`,
      })
    }
    let regexValid = true
    const metadataEnable = Utils.getFlagsmithHasFeature('enable_metadata')
    try {
      if (!isEdit && name && regex) {
        regexValid = name.match(new RegExp(regex))
      }
    } catch (e) {
      regexValid = false
    }
    const Settings = (projectAdmin, createFeature, featureContentType) => (
      <>
        {!identity && this.state.tags && (
          <FormGroup className='mb-5 setting'>
            <InputGroup
              title={identity ? 'Tags' : 'Tags (optional)'}
              tooltip={Constants.strings.TAGS_DESCRIPTION}
              component={
                <AddEditTags
                  readOnly={!!identity || !createFeature}
                  projectId={`${this.props.projectId}`}
                  value={this.state.tags}
                  onChange={(tags) =>
                    this.setState({ settingsChanged: true, tags })
                  }
                />
              }
            />
          </FormGroup>
        )}
        {metadataEnable && featureContentType?.id && (
          <FormGroup className='mb-5 setting'>
            <InputGroup
              title={'Metadata'}
              tooltip={`${Constants.strings.TOOLTIP_METADATA_DESCRIPTION} feature`}
              tooltipPlace='right'
              component={
                <AddMetadataToEntity
                  organisationId={AccountStore.getOrganisation().id}
                  projectId={this.props.projectId}
                  entityId={projectFlag?.id}
                  entityContentType={featureContentType?.id}
                  entity={featureContentType?.model}
                  setHasMetadataRequired={(b) => {
                    this.setState({
                      hasMetadataRequired: true,
                    })
                  }}
                  onChange={(m) => {
                    this.setState({
                      metadata: m,
                    })
                  }}
                />
              }
            />
          </FormGroup>
        )}
        {!identity && projectFlag && (
          <Permission
            level='project'
            permission='ADMIN'
            id={this.props.projectId}
          >
            {({ permission: projectAdmin }) =>
              projectAdmin && (
                <>
                  <FormGroup className='mb-5 setting'>
                    <FlagOwners
                      projectId={this.props.projectId}
                      id={projectFlag.id}
                    />
                  </FormGroup>
                  <FormGroup className='mb-5 setting'>
                    <FlagOwnerGroups
                      projectId={this.props.projectId}
                      id={projectFlag.id}
                    />
                  </FormGroup>
                </>
              )
            }
          </Permission>
        )}
        <FormGroup className='mb-5 setting'>
          <InputGroup
            value={description}
            data-test='featureDesc'
            inputProps={{
              className: 'full-width',
              name: 'featureDesc',
            }}
            onChange={(e) =>
              this.setState({
                description: Utils.safeParseEventValue(e),
                settingsChanged: true,
              })
            }
            ds
            type='text'
            title={identity ? 'Description' : 'Description (optional)'}
            placeholder="e.g. 'This determines what size the header is' "
          />
        </FormGroup>
        {Utils.getFlagsmithHasFeature('github_integration') &&
          hasIntegrationWithGithub &&
          projectFlag?.id && (
            <>
              <FormGroup className='mt-4 setting'>
                <label className='cols-sm-2 control-label'>
                  {' '}
                  GitHub Repositories
                </label>
                <MyRepositoriesSelect
                  githubId={githubId}
                  orgId={AccountStore.getOrganisation().id}
                  onChange={(v) => {
                    const repoData = v.split('/')
                    this.setState({
                      repoName: repoData[0],
                      repoOwner: repoData[1],
                    })
                  }}
                />
                {repoName && repoOwner && (
                  <>
                    <label className='cols-sm-2 control-label mt-4'>
                      {' '}
                      Link GitHub Issue Pull-Request
                    </label>
                    <Row className='cols-md-2 role-list'>
                      <div style={{ width: '200px' }}>
                        <Select
                          size='select-md'
                          placeholder={'Select Type'}
                          onChange={(v) =>
                            this.setState({ externalResourceType: v.label })
                          }
                          options={[
                            { id: 1, type: 'Github Issue' },
                            { id: 2, type: 'Github PR' },
                          ].map((e) => {
                            return { label: e.type, value: e.id }
                          })}
                        />
                      </div>
                      <Flex className='ml-4'>
                        {externalResourceType == 'Github Issue' ? (
                          <MyIssueSelect
                            orgId={AccountStore.getOrganisation().id}
                            onChange={(v) =>
                              this.setState({
                                featureExternalResource: v,
                                status: 'open',
                              })
                            }
                            repoOwner={repoOwner}
                            repoName={repoName}
                          />
                        ) : externalResourceType == 'Github PR' ? (
                          <MyPullRequestsSelect
                            orgId={AccountStore.getOrganisation().id}
                            onChange={(v) =>
                              this.setState({
                                featureExternalResource: v.value,
                              })
                            }
                            repoOwner={repoOwner}
                            repoName={repoName}
                          />
                        ) : (
                          <></>
                        )}
                      </Flex>
                      {(externalResourceType == 'Github Issue' ||
                        externalResourceType == 'Github PR') && (
                        <Button
                          className='text-right'
                          theme='primary'
                          onClick={() => {
                            _createExternalResourse()
                          }}
                        >
                          Link
                        </Button>
                      )}
                    </Row>
                  </>
                )}
              </FormGroup>
              <ExternalResourcesTable
                featureId={projectFlag.id}
                projectId={`${this.props.projectId}`}
              />
            </>
          )}

        {!identity && (
          <FormGroup className='mb-5 mt-3 setting'>
            <Row>
              <Switch
                checked={this.state.is_server_key_only}
                onChange={(is_server_key_only) =>
                  this.setState({ is_server_key_only, settingsChanged: true })
                }
                className='ml-0'
              />
              <Tooltip
                title={
                  <label className='cols-sm-2 control-label mb-0 ml-3'>
                    Server-side only <Icon name='info-outlined' />
                  </label>
                }
              >
                Prevent this feature from being accessed with client-side SDKs.
              </Tooltip>
            </Row>
          </FormGroup>
        )}

        {!identity && isEdit && (
          <FormGroup className='mb-5 setting'>
            <Row>
              <Switch
                checked={this.state.is_archived}
                onChange={(is_archived) => {
                  this.setState({ is_archived, settingsChanged: true })
                }}
                className='ml-0'
              />
              <Tooltip
                title={
                  <label className='cols-sm-2 control-label mb-0 ml-3'>
                    Archived <Icon name='info-outlined' />
                  </label>
                }
              >
                {`Archiving a flag allows you to filter out flags from the
                Flagsmith dashboard that are no longer relevant.
                <br />
                An archived flag will still return as normal in all SDK
                endpoints.`}
              </Tooltip>
            </Row>
          </FormGroup>
        )}
      </>
    )

    const Value = (error, projectAdmin, createFeature, hideValue) => (
      <>
        {!!isEdit && (
          <ExistingChangeRequestAlert
            className='mb-4'
            featureId={projectFlag.id}
            environmentId={this.props.environmentId}
          />
        )}
        {!isEdit && (
          <FormGroup className='mb-4 mt-2'>
            <InputGroup
              ref={(e) => (this.input = e)}
              data-test='featureID'
              inputProps={{
                className: 'full-width',
                maxLength: FEATURE_ID_MAXLENGTH,
                name: 'featureID',
                readOnly: isEdit,
              }}
              value={name}
              onChange={(e) => {
                const newName = Utils.safeParseEventValue(e).replace(/ /g, '_')
                this.setState({
                  name: caseSensitive ? newName.toLowerCase() : newName,
                })
              }}
              isValid={!!name && regexValid}
              type='text'
              title={
                <>
                  <Tooltip
                    title={
                      <Row>
                        <span className={'mr-1'}>
                          {isEdit ? 'ID / Name' : 'ID / Name*'}
                        </span>
                        <Icon name='info-outlined' />
                      </Row>
                    }
                  >
                    The ID that will be used by SDKs to retrieve the feature
                    value and enabled state. This cannot be edited once the
                    feature has been created.
                  </Tooltip>
                  {!!regex && !isEdit && (
                    <div className='mt-2'>
                      {' '}
                      <InfoMessage>
                        {' '}
                        This must conform to the regular expression{' '}
                        <pre>{regex}</pre>
                      </InfoMessage>
                    </div>
                  )}
                </>
              }
              placeholder='E.g. header_size'
            />
            <ErrorMessage error={error?.name?.[0]} />
          </FormGroup>
        )}

        {identity && description && (
          <FormGroup className='mb-4 mt-2 mx-3'>
            <InputGroup
              value={description}
              data-test='featureDesc'
              inputProps={{
                className: 'full-width',
                name: 'featureDesc',
                readOnly: !!identity || noPermissions,
                valueChanged: true,
              }}
              onChange={(e) =>
                this.setState({ description: Utils.safeParseEventValue(e) })
              }
              type='text'
              title={identity ? 'Description' : 'Description (optional)'}
              placeholder='No description'
            />
          </FormGroup>
        )}
        {!hideValue && (
          <div
            className={`${identity && !description ? 'mt-4 mx-3' : ''} ${
              identity ? 'mx-3' : ''
            }`}
          >
            <Feature
              readOnly={noPermissions}
              multivariate_options={multivariate_options}
              environmentVariations={environmentVariations}
              isEdit={isEdit}
              error={error?.initial_value?.[0]}
              canCreateFeature={createFeature}
              identity={identity}
              removeVariation={this.removeVariation}
              updateVariation={this.updateVariation}
              addVariation={this.addVariation}
              checked={default_enabled}
              value={initial_value}
              identityVariations={this.state.identityVariations}
              onChangeIdentityVariations={(identityVariations) => {
                this.setState({ identityVariations, valueChanged: true })
              }}
              environmentFlag={this.state.environmentFlag}
              projectFlag={projectFlag}
              onValueChange={(e) => {
                const initial_value = Utils.getTypedValue(
                  Utils.safeParseEventValue(e),
                )
                this.setState({ initial_value, valueChanged: true })
              }}
              onCheckedChange={(default_enabled) =>
                this.setState({ default_enabled })
              }
            />
          </div>
        )}
        {!isEdit &&
          !identity &&
          Settings(projectAdmin, createFeature, featureContentType)}
      </>
    )
    return (
      <ProjectProvider id={this.props.projectId}>
        {({ project }) => (
          <Provider
            onSave={() => {
              if (identity) {
                this.close()
              }
              AppActions.refreshFeatures(
                this.props.projectId,
                this.props.environmentId,
              )
            }}
          >
            {(
              { error, isSaving, usageData },
              {
                createChangeRequest,
                createFlag,
                editFeatureSegments,
                editFeatureSettings,
                editFeatureValue,
              },
            ) => {
              const saveFeatureValue = (schedule) => {
                this.setState({ valueChanged: false })
                if ((is4Eyes || schedule) && !identity) {
                  openModal2(
                    schedule
                      ? 'New Scheduled Flag Update'
                      : this.props.changeRequest
                      ? 'Update Change Request'
                      : 'New Change Request',
                    <ChangeRequestModal
                      showAssignees={is4Eyes}
                      changeRequest={this.props.changeRequest}
                      onSave={({
                        approvals,
                        description,
                        live_from,
                        title,
                      }) => {
                        closeModal2()
                        this.save(
                          (
                            projectId,
                            environmentId,
                            flag,
                            projectFlag,
                            environmentFlag,
                            segmentOverrides,
                          ) => {
                            createChangeRequest(
                              projectId,
                              environmentId,
                              flag,
                              projectFlag,
                              environmentFlag,
                              segmentOverrides,
                              {
                                approvals,
                                description,
                                featureStateId:
                                  this.props.changeRequest &&
                                  this.props.changeRequest.feature_states[0].id,
                                id:
                                  this.props.changeRequest &&
                                  this.props.changeRequest.id,
                                live_from,
                                multivariate_options: this.props
                                  .multivariate_options
                                  ? this.props.multivariate_options.map((v) => {
                                      const matching =
                                        this.state.multivariate_options.find(
                                          (m) =>
                                            m.id ===
                                            v.multivariate_feature_option,
                                        )
                                      return {
                                        ...v,
                                        percentage_allocation:
                                          matching.default_percentage_allocation,
                                      }
                                    })
                                  : this.state.multivariate_options,
                                title,
                              },
                              !is4Eyes,
                              'VALUE',
                            )
                          },
                        )
                      }}
                    />,
                  )
                } else if (
                  document.getElementById('language-validation-error')
                ) {
                  openConfirm({
                    body: 'Your remote config value does not pass validation for the language you have selected. Are you sure you wish to save?',
                    noText: 'Cancel',
                    onYes: () => {
                      this.save(editFeatureValue, isSaving)
                    },
                    title: 'Validation error',
                    yesText: 'Save',
                  })
                } else {
                  this.save(editFeatureValue, isSaving)
                }
              }

              const saveSettings = () => {
                this.setState({ settingsChanged: false })
                this.save(editFeatureSettings, isSaving)
              }

              const saveFeatureSegments = () => {
                this.setState({ segmentsChanged: false })

                if (is4Eyes && isVersioned && !identity) {
                  openModal2(
                    this.props.changeRequest
                      ? 'Update Change Request'
                      : 'New Change Request',
                    <ChangeRequestModal
                      showAssignees={is4Eyes}
                      changeRequest={this.props.changeRequest}
                      onSave={({
                        approvals,
                        description,
                        live_from,
                        title,
                      }) => {
                        closeModal2()
                        this.save(
                          (
                            projectId,
                            environmentId,
                            flag,
                            projectFlag,
                            environmentFlag,
                            segmentOverrides,
                          ) => {
                            createChangeRequest(
                              projectId,
                              environmentId,
                              flag,
                              projectFlag,
                              environmentFlag,
                              segmentOverrides,
                              {
                                approvals,
                                description,
                                featureStateId:
                                  this.props.changeRequest &&
                                  this.props.changeRequest.feature_states[0].id,
                                id:
                                  this.props.changeRequest &&
                                  this.props.changeRequest.id,
                                live_from,
                                multivariate_options: this.props
                                  .multivariate_options
                                  ? this.props.multivariate_options.map((v) => {
                                      const matching =
                                        this.state.multivariate_options.find(
                                          (m) =>
                                            m.id ===
                                            v.multivariate_feature_option,
                                        )
                                      return {
                                        ...v,
                                        percentage_allocation:
                                          matching.default_percentage_allocation,
                                      }
                                    })
                                  : this.state.multivariate_options,
                                title,
                              },
                              !is4Eyes,
                              'SEGMENT',
                            )
                          },
                        )
                      }}
                    />,
                  )
                } else {
                  this.save(editFeatureSegments, isSaving)
                }
              }

              const onCreateFeature = () => {
                this.save(createFlag, isSaving)
              }

              const featureLimitAlert =
                Utils.calculateRemainingLimitsPercentage(
                  project.total_features,
                  project.max_features_allowed,
                )

              return (
                <Permission
                  level='project'
                  permission='CREATE_FEATURE'
                  id={this.props.projectId}
                >
                  {({ permission: createFeature }) => (
                    <Permission
                      level='project'
                      permission='ADMIN'
                      id={this.props.projectId}
                    >
                      {({ permission: projectAdmin }) => {
                        this.state.skipSaveProjectFeature = !createFeature
                        const _hasMetadataRequired =
                          this.state.hasMetadataRequired &&
                          !this.state.metadata.length
                        return (
                          <div id='create-feature-modal'>
                            {isEdit && !identity ? (
                              <Tabs
                                onChange={() => this.forceUpdate()}
                                history={this.props.history}
                                urlParam='tab'
                              >
                                <TabItem
                                  data-test='value'
                                  tabLabelString='Value'
                                  tabLabel={
                                    <Row className='justify-content-center'>
                                      Value{' '}
                                      {this.state.valueChanged && (
                                        <div className='unread ml-2 px-1'>
                                          {'*'}
                                        </div>
                                      )}
                                    </Row>
                                  }
                                >
                                  <FormGroup>
                                    {featureLimitAlert.percentage &&
                                      Utils.displayLimitAlert(
                                        'features',
                                        featureLimitAlert.percentage,
                                      )}
                                    <Tooltip
                                      title={
                                        <h5 className='mb-4'>
                                          Environment Value{' '}
                                          <Icon name='info-outlined' />
                                        </h5>
                                      }
                                      place='top'
                                    >
                                      {Constants.strings.ENVIRONMENT_OVERRIDE_DESCRIPTION(
                                        _.find(project.environments, {
                                          api_key: this.props.environmentId,
                                        }).name,
                                      )}
                                    </Tooltip>
                                    {Value(error, projectAdmin, createFeature)}

                                    {isEdit && (
                                      <>
                                        <JSONReference
                                          showNamesButton
                                          title={'Feature'}
                                          json={projectFlag}
                                        />
                                        <JSONReference
                                          title={'Feature state'}
                                          json={this.state.environmentFlag}
                                        />
                                      </>
                                    )}
                                    <ModalHR className='mt-4' />
                                    <div className='text-right mt-4 mb-3 fs-small lh-sm modal-caption'>
                                      {is4Eyes
                                        ? 'This will create a change request for the environment'
                                        : 'This will update the feature value for the environment'}{' '}
                                      <strong>
                                        {
                                          _.find(project.environments, {
                                            api_key: this.props.environmentId,
                                          }).name
                                        }
                                      </strong>
                                    </div>

                                    <Permission
                                      level='environment'
                                      permission={Utils.getManageFeaturePermission(
                                        is4Eyes,
                                        identity,
                                      )}
                                      id={this.props.environmentId}
                                    >
                                      {({ permission: savePermission }) =>
                                        Utils.renderWithPermission(
                                          savePermission,
                                          Constants.environmentPermissions(
                                            Utils.getManageFeaturePermissionDescription(
                                              is4Eyes,
                                              identity,
                                            ),
                                          ),
                                          <div className='text-right'>
                                            {!is4Eyes && (
                                              <>
                                                {canSchedule ? (
                                                  <Button
                                                    theme='secondary'
                                                    onClick={() =>
                                                      saveFeatureValue(true)
                                                    }
                                                    className='mr-2'
                                                    type='button'
                                                    data-test='create-change-request'
                                                    id='create-change-request-btn'
                                                    disabled={
                                                      isSaving ||
                                                      !name ||
                                                      invalid ||
                                                      !savePermission
                                                    }
                                                  >
                                                    {isSaving
                                                      ? existingChangeRequest
                                                        ? 'Updating Change Request'
                                                        : 'Scheduling Update'
                                                      : existingChangeRequest
                                                      ? 'Update Change Request'
                                                      : 'Schedule Update'}
                                                  </Button>
                                                ) : (
                                                  <Tooltip
                                                    title={
                                                      <Button
                                                        theme='outline'
                                                        disabled
                                                        className='mr-2'
                                                        type='button'
                                                        data-test='create-change-request'
                                                        id='create-change-request-btn'
                                                      >
                                                        {isSaving
                                                          ? existingChangeRequest
                                                            ? 'Updating Change Request'
                                                            : 'Scheduling Update'
                                                          : existingChangeRequest
                                                          ? 'Update Change Request'
                                                          : 'Schedule Update'}
                                                      </Button>
                                                    }
                                                  >
                                                    {
                                                      'This feature is available on our start-up plan'
                                                    }
                                                  </Tooltip>
                                                )}
                                              </>
                                            )}

                                            {is4Eyes ? (
                                              <Button
                                                onClick={() =>
                                                  saveFeatureValue()
                                                }
                                                type='button'
                                                data-test='update-feature-btn'
                                                id='update-feature-btn'
                                                disabled={
                                                  !savePermission ||
                                                  isSaving ||
                                                  !name ||
                                                  invalid
                                                }
                                              >
                                                {isSaving
                                                  ? existingChangeRequest
                                                    ? 'Updating Change Request'
                                                    : 'Creating Change Request'
                                                  : existingChangeRequest
                                                  ? 'Update Change Request'
                                                  : 'Create Change Request'}
                                              </Button>
                                            ) : (
                                              <Button
                                                onClick={() =>
                                                  saveFeatureValue()
                                                }
                                                type='button'
                                                data-test='update-feature-btn'
                                                id='update-feature-btn'
                                                disabled={
                                                  isSaving ||
                                                  !name ||
                                                  invalid ||
                                                  !savePermission
                                                }
                                              >
                                                {isSaving
                                                  ? 'Updating'
                                                  : 'Update Feature Value'}
                                              </Button>
                                            )}
                                          </div>,
                                        )
                                      }
                                    </Permission>
                                  </FormGroup>
                                </TabItem>
                                {!existingChangeRequest && (
                                  <TabItem
                                    data-test='segment_overrides'
                                    tabLabelString='Segment Overrides'
                                    tabLabel={
                                      <Row
                                        className={`justify-content-center ${
                                          this.state.segmentsChanged
                                            ? 'pr-1'
                                            : ''
                                        }`}
                                      >
                                        Segment Overrides{' '}
                                        {this.state.segmentsChanged && (
                                          <div className='unread ml-2 px-2'>
                                            *
                                          </div>
                                        )}
                                      </Row>
                                    }
                                  >
                                    {!identity && isEdit && (
                                      <FormGroup className='mb-4'>
                                        <div>
                                          <Row className='justify-content-between mb-2 segment-overrides-title'>
                                            <Tooltip
                                              title={
                                                <h5 className='mb-0'>
                                                  Segment Overrides{' '}
                                                  <Icon name='info-outlined' />
                                                </h5>
                                              }
                                              place='top'
                                            >
                                              {
                                                Constants.strings
                                                  .SEGMENT_OVERRIDES_DESCRIPTION
                                              }
                                            </Tooltip>
                                            {!this.state.showCreateSegment &&
                                              !noPermissions && (
                                                <Button
                                                  onClick={() =>
                                                    this.changeSegment(
                                                      this.props
                                                        .segmentOverrides,
                                                    )
                                                  }
                                                  type='button'
                                                  theme='secondary'
                                                  size='small'
                                                >
                                                  {enabledSegment
                                                    ? 'Enable All'
                                                    : 'Disable All'}
                                                </Button>
                                              )}
                                          </Row>
                                          {this.props.segmentOverrides ? (
                                            <Permission
                                              level='environment'
                                              permission={
                                                'MANAGE_SEGMENT_OVERRIDES'
                                              }
                                              id={this.props.environmentId}
                                            >
                                              {({
                                                permission:
                                                  manageSegmentOverrides,
                                              }) => {
                                                const isReadOnly =
                                                  !manageSegmentOverrides
                                                return (
                                                  <SegmentOverrides
                                                    readOnly={isReadOnly}
                                                    showEditSegment
                                                    showCreateSegment={
                                                      this.state
                                                        .showCreateSegment
                                                    }
                                                    setShowCreateSegment={(
                                                      showCreateSegment,
                                                    ) =>
                                                      this.setState({
                                                        showCreateSegment,
                                                      })
                                                    }
                                                    feature={projectFlag.id}
                                                    projectId={
                                                      this.props.projectId
                                                    }
                                                    multivariateOptions={
                                                      multivariate_options
                                                    }
                                                    environmentId={
                                                      this.props.environmentId
                                                    }
                                                    value={
                                                      this.props
                                                        .segmentOverrides
                                                    }
                                                    controlValue={initial_value}
                                                    onChange={(v) => {
                                                      this.setState({
                                                        segmentsChanged: true,
                                                      })
                                                      this.props.updateSegments(
                                                        v,
                                                      )
                                                    }}
                                                  />
                                                )
                                              }}
                                            </Permission>
                                          ) : (
                                            <div className='text-center'>
                                              <Loader />
                                            </div>
                                          )}
                                          {!this.state.showCreateSegment && (
                                            <ModalHR className='mt-4' />
                                          )}
                                          {!this.state.showCreateSegment && (
                                            <div>
                                              <p className='text-right mt-4 fs-small lh-sm modal-caption'>
                                                {is4Eyes && isVersioned
                                                  ? 'This will create a change request for the environment'
                                                  : 'This will update the segment overrides for the environment'}{' '}
                                                <strong>
                                                  {
                                                    _.find(
                                                      project.environments,
                                                      {
                                                        api_key:
                                                          this.props
                                                            .environmentId,
                                                      },
                                                    ).name
                                                  }
                                                </strong>
                                              </p>
                                              <div className='text-right'>
                                                <Permission
                                                  level='environment'
                                                  permission={Utils.getManageFeaturePermission(
                                                    is4Eyes,
                                                    identity,
                                                  )}
                                                  id={this.props.environmentId}
                                                >
                                                  {({
                                                    permission: savePermission,
                                                  }) => (
                                                    <Permission
                                                      level='environment'
                                                      permission={
                                                        'MANAGE_SEGMENT_OVERRIDES'
                                                      }
                                                      id={
                                                        this.props.environmentId
                                                      }
                                                    >
                                                      {({
                                                        permission:
                                                          manageSegmentsOverrides,
                                                      }) => {
                                                        if (
                                                          isVersioned &&
                                                          is4Eyes
                                                        ) {
                                                          return Utils.renderWithPermission(
                                                            savePermission,
                                                            Utils.getManageFeaturePermissionDescription(
                                                              is4Eyes,
                                                              identity,
                                                            ),
                                                            <Button
                                                              onClick={
                                                                saveFeatureSegments
                                                              }
                                                              type='button'
                                                              data-test='update-feature-segments-btn'
                                                              id='update-feature-segments-btn'
                                                              disabled={
                                                                isSaving ||
                                                                !name ||
                                                                invalid ||
                                                                !savePermission
                                                              }
                                                            >
                                                              {isSaving
                                                                ? existingChangeRequest
                                                                  ? 'Updating Change Request'
                                                                  : 'Creating Change Request'
                                                                : existingChangeRequest
                                                                ? 'Update Change Request'
                                                                : 'Create Change Request'}
                                                            </Button>,
                                                          )
                                                        }

                                                        return Utils.renderWithPermission(
                                                          manageSegmentsOverrides,
                                                          Constants.environmentPermissions(
                                                            'Manage segment overrides',
                                                          ),
                                                          <Button
                                                            onClick={
                                                              saveFeatureSegments
                                                            }
                                                            type='button'
                                                            data-test='update-feature-segments-btn'
                                                            id='update-feature-segments-btn'
                                                            disabled={
                                                              isSaving ||
                                                              !name ||
                                                              invalid ||
                                                              !manageSegmentsOverrides
                                                            }
                                                          >
                                                            {isSaving
                                                              ? 'Updating'
                                                              : 'Update Segment Overrides'}
                                                          </Button>,
                                                        )
                                                      }}
                                                    </Permission>
                                                  )}
                                                </Permission>
                                              </div>
                                            </div>
                                          )}
                                        </div>
                                      </FormGroup>
                                    )}
                                  </TabItem>
                                )}

                                {!identity &&
                                  isEdit &&
                                  !existingChangeRequest &&
                                  !hideIdentityOverridesTab && (
                                    <TabItem
                                      data-test='identity_overrides'
                                      tabLabel='Identity Overrides'
                                    >
                                      <InfoMessage className='mb-4 text-left faint'>
                                        Identity overrides override feature
                                        values for individual identities. The
                                        overrides take priority over an segment
                                        overrides and environment defaults.
                                        Identity overrides will only apply when
                                        you identify via the SDK.{' '}
                                        <a
                                          target='_blank'
                                          href='https://docs.flagsmith.com/basic-features/managing-identities'
                                          rel='noreferrer'
                                        >
                                          Check the Docs for more details
                                        </a>
                                        .
                                      </InfoMessage>
                                      <FormGroup className='mb-4'>
                                        <PanelSearch
                                          id='users-list'
                                          className='no-pad identity-overrides-title'
                                          title={
                                            <Tooltip
                                              title={
                                                <h5 className='mb-0'>
                                                  Identity Overrides{' '}
                                                  <Icon
                                                    name='info-outlined'
                                                    width={20}
                                                    fill='#9DA4AE'
                                                  />
                                                </h5>
                                              }
                                              place='top'
                                            >
                                              {
                                                Constants.strings
                                                  .IDENTITY_OVERRIDES_DESCRIPTION
                                              }
                                            </Tooltip>
                                          }
                                          action={
                                            !Utils.getIsEdge() && (
                                              <Button
                                                onClick={() =>
                                                  this.changeIdentity(
                                                    this.state.userOverrides,
                                                  )
                                                }
                                                type='button'
                                                theme='secondary'
                                                size='small'
                                              >
                                                {enabledIndentity
                                                  ? 'Enable All'
                                                  : 'Disable All'}
                                              </Button>
                                            )
                                          }
                                          items={this.state.userOverrides}
                                          paging={
                                            this.state.userOverridesPaging
                                          }
                                          renderSearchWithNoResults
                                          nextPage={() =>
                                            this.userOverridesPage(
                                              this.state.userOverridesPaging
                                                .currentPage + 1,
                                            )
                                          }
                                          prevPage={() =>
                                            this.userOverridesPage(
                                              this.state.userOverridesPaging
                                                .currentPage - 1,
                                            )
                                          }
                                          goToPage={(page) =>
                                            this.userOverridesPage(page)
                                          }
                                          searchPanel={
                                            !Utils.getIsEdge() && (
                                              <div className='text-center mt-2 mb-2'>
                                                <Flex className='text-left'>
                                                  <IdentitySelect
                                                    isEdge={false}
                                                    ignoreIds={this.state.userOverrides?.map(
                                                      (v) => v.identity?.id,
                                                    )}
                                                    environmentId={
                                                      this.props.environmentId
                                                    }
                                                    data-test='select-identity'
                                                    placeholder='Create an Identity Override...'
                                                    value={
                                                      this.state
                                                        .selectedIdentity
                                                    }
                                                    onChange={(
                                                      selectedIdentity,
                                                    ) =>
                                                      this.setState(
                                                        { selectedIdentity },
                                                        this.addItem,
                                                      )
                                                    }
                                                  />
                                                </Flex>
                                              </div>
                                            )
                                          }
                                          renderRow={(identityFlag) => {
                                            const {
                                              enabled,
                                              feature_state_value,
                                              id,
                                              identity,
                                            } = identityFlag
                                            return (
                                              <Row
                                                space
                                                className='list-item cursor-pointer'
                                                key={id}
                                              >
                                                <Row>
                                                  <div
                                                    className='table-column'
                                                    style={{ width: '65px' }}
                                                  >
                                                    <Switch
                                                      checked={enabled}
                                                      onChange={() =>
                                                        this.toggleUserFlag({
                                                          enabled,
                                                          id,
                                                          identity,
                                                        })
                                                      }
                                                      disabled={Utils.getIsEdge()}
                                                    />
                                                  </div>
                                                  <div className='font-weight-medium fs-small lh-sm'>
                                                    {identity.identifier}
                                                  </div>
                                                </Row>
                                                <Row>
                                                  <div
                                                    className='table-column'
                                                    style={{ width: '188px' }}
                                                  >
                                                    {feature_state_value !==
                                                      null && (
                                                      <FeatureValue
                                                        value={
                                                          feature_state_value
                                                        }
                                                      />
                                                    )}
                                                  </div>
                                                  <div className='table-column'>
                                                    <Button
                                                      target='_blank'
                                                      href={`/project/${this.props.projectId}/environment/${this.props.environmentId}/users/${identity.identifier}/${identity.id}?flag=${projectFlag.name}`}
                                                      className='btn btn-link fs-small lh-sm font-weight-medium'
                                                    >
                                                      <Icon
                                                        name='edit'
                                                        width={20}
                                                        fill='#6837FC'
                                                      />{' '}
                                                      Edit
                                                    </Button>
                                                    <Button
                                                      onClick={(e) => {
                                                        e.stopPropagation()
                                                        removeUserOverride({
                                                          cb: () =>
                                                            this.userOverridesPage(
                                                              1,
                                                            ),
                                                          environmentId:
                                                            this.props
                                                              .environmentId,
                                                          identifier:
                                                            identity.identifier,
                                                          identity: identity.id,
                                                          identityFlag,
                                                          projectFlag,
                                                        })
                                                      }}
                                                      className='btn ml-2 btn-with-icon'
                                                    >
                                                      <Icon
                                                        name='trash-2'
                                                        width={20}
                                                        fill='#656D7B'
                                                      />
                                                    </Button>
                                                  </div>
                                                </Row>
                                              </Row>
                                            )
                                          }}
                                          renderNoResults={
                                            <Row className='list-item'>
                                              <div className='table-column'>
                                                No identities are overriding
                                                this feature.
                                              </div>
                                            </Row>
                                          }
                                          isLoading={!this.state.userOverrides}
                                        />
                                      </FormGroup>
                                    </TabItem>
                                  )}
                                {!existingChangeRequest &&
                                  !Project.disableAnalytics &&
                                  this.props.flagId && (
                                    <TabItem
                                      data-test='analytics'
                                      tabLabel='Analytics'
                                    >
                                      <FormGroup className='mb-4'>
                                        {!!usageData && (
                                          <h5 className='mb-2'>
                                            Flag events for last 30 days
                                          </h5>
                                        )}
                                        {!usageData && (
                                          <div className='text-center'>
                                            <Loader />
                                          </div>
                                        )}

                                        {this.drawChart(usageData)}
                                      </FormGroup>
                                      <InfoMessage>
                                        The Flag Analytics data will be visible
                                        in the Dashboard between 30 minutes and
                                        1 hour after it has been collected.{' '}
                                        <a
                                          target='_blank'
                                          href='https://docs.flagsmith.com/advanced-use/flag-analytics'
                                          rel='noreferrer'
                                        >
                                          View docs
                                        </a>
                                      </InfoMessage>
                                    </TabItem>
                                  )}
                                {!existingChangeRequest && createFeature && (
                                  <TabItem
                                    data-test='settings'
                                    tabLabelString='Settings'
                                    tabLabel={
                                      <Row className='justify-content-center'>
                                        Settings{' '}
                                        {this.state.settingsChanged && (
                                          <div className='unread ml-2 px-1'>
                                            {'*'}
                                          </div>
                                        )}
                                      </Row>
                                    }
                                  >
                                    {Settings(
                                      projectAdmin,
                                      createFeature,
                                      featureContentType,
                                    )}
                                    <JSONReference
                                      className='mb-3'
                                      showNamesButton
                                      title={'Feature'}
                                      json={projectFlag}
                                    />
                                    <ModalHR className='mt-4' />
                                    {isEdit && (
                                      <div className='text-right mt-3'>
                                        {createFeature ? (
                                          <p className='text-right modal-caption fs-small lh-sm'>
                                            This will save the above settings{' '}
                                            <strong>all environments</strong>.
                                          </p>
                                        ) : (
                                          <p className='text-right modal-caption fs-small lh-sm'>
                                            To edit this feature's settings, you
                                            will need{' '}
                                            <strong>
                                              Project Administrator permissions
                                            </strong>
                                            . Please contact your project
                                            administrator.
                                          </p>
                                        )}

                                        {createFeature ? (
                                          <Button
                                            onClick={saveSettings}
                                            data-test='update-feature-btn'
                                            id='update-feature-btn'
                                            disabled={
                                              isSaving ||
                                              !name ||
                                              invalid ||
                                              _hasMetadataRequired
                                            }
                                          >
                                            {isSaving
                                              ? 'Updating'
                                              : 'Update Settings'}
                                          </Button>
                                        ) : null}
                                      </div>
                                    )}
                                  </TabItem>
                                )}
                              </Tabs>
                            ) : (
                              <div
                                className={classNames(
                                  !isEdit ? 'create-feature-tab px-3' : '',
                                )}
                              >
                                {featureLimitAlert.percentage &&
                                  Utils.displayLimitAlert(
                                    'features',
                                    featureLimitAlert.percentage,
                                  )}
                                {Value(
                                  error,
                                  projectAdmin,
                                  createFeature,
                                  project.prevent_flag_defaults,
                                )}
                                <ModalHR
                                  className={`my-4 ${identity ? 'mx-3' : ''}`}
                                />
                                {!identity && (
                                  <div className='text-right mb-3'>
                                    {project.prevent_flag_defaults ? (
                                      <InfoMessage className='text-right modal-caption fs-small lh-sm'>
                                        This will create the feature for{' '}
                                        <strong>all environments</strong>, you
                                        can edit this feature per environment
                                        once the feature's enabled state and
                                        environment once the feature is created.
                                      </InfoMessage>
                                    ) : (
                                      <InfoMessage className='text-right modal-caption fs-small lh-sm'>
                                        This will create the feature for{' '}
                                        <strong>all environments</strong>, you
                                        can edit this feature per environment
                                        once the feature is created.
                                      </InfoMessage>
                                    )}

                                    <Button
                                      onClick={onCreateFeature}
                                      data-test='create-feature-btn'
                                      id='create-feature-btn'
                                      disabled={
                                        isSaving ||
                                        !name ||
                                        invalid ||
                                        !regexValid ||
                                        featureLimitAlert.percentage >= 100 ||
                                        _hasMetadataRequired
                                      }
                                    >
                                      {isSaving ? 'Creating' : 'Create Feature'}
                                    </Button>
                                  </div>
                                )}
                              </div>
                            )}
                            {identity && (
                              <div className='pr-3'>
                                {identity ? (
                                  <div className='mb-3 mt-4'>
                                    <p className='text-left ml-3 modal-caption fs-small lh-small'>
                                      This will update the feature value for the
                                      user <strong>{identityName}</strong> in
                                      <strong>
                                        {' '}
                                        {
                                          _.find(project.environments, {
                                            api_key: this.props.environmentId,
                                          }).name
                                        }
                                        .
                                      </strong>
                                      {
                                        ' Any segment overrides for this feature will now be ignored.'
                                      }
                                    </p>
                                  </div>
                                ) : (
                                  ''
                                )}

                                <div className='text-right mb-2'>
                                  {identity && (
                                    <div>
                                      <Button
                                        onClick={() => saveFeatureValue()}
                                        data-test='update-feature-btn'
                                        id='update-feature-btn'
                                        disabled={isSaving || !name || invalid}
                                      >
                                        {isSaving
                                          ? 'Updating'
                                          : 'Update Feature'}
                                      </Button>
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        )
                      }}
                    </Permission>
                  )}
                </Permission>
              )
            }}
          </Provider>
        )}
      </ProjectProvider>
    )
  }
}

CreateFlag.propTypes = {}

//This will remount the modal when a feature is created
const FeatureProvider = (WrappedComponent) => {
  class HOC extends Component {
    static contextTypes = {
      router: propTypes.object.isRequired,
    }

    constructor(props) {
      super(props)
      this.state = {
        ...props,
      }
      ES6Component(this)
    }

    componentDidMount() {
      // toast update feature
      ES6Component(this)
      this.listenTo(
        FeatureListStore,
        'saved',
        ({ changeRequest, createdFlag, isCreate } = {}) => {
          toast(
            `${createdFlag || isCreate ? 'Created' : 'Updated'} ${
              changeRequest ? 'Change Request' : 'Feature'
            }`,
          )
          if (createdFlag) {
            const projectFlag = FeatureListStore.getProjectFlags()?.find?.(
              (flag) => flag.name === createdFlag,
            )
            window.history.replaceState(
              {},
              `${document.location.pathname}?feature=${projectFlag.id}`,
            )
            const envFlags = FeatureListStore.getEnvironmentFlags()
            const newEnvironmentFlag = envFlags?.[projectFlag.id] || {}
            setModalTitle(`Edit Feature ${projectFlag.name}`)
            this.setState({
              environmentFlag: {
                ...this.state.environmentFlag,
                ...(newEnvironmentFlag || {}),
              },
              projectFlag,
            })
          }
          if (changeRequest) {
            closeModal()
          }
        },
      )
    }

    render() {
      return (
        <WrappedComponent
          key={this.state.projectFlag?.id || 'new'}
          {...this.state}
        />
      )
    }
  }
  return HOC
}

export default FeatureProvider(ConfigProvider(withSegmentOverrides(CreateFlag)))
