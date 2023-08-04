import React, { Component } from 'react'
import ConfirmToggleFeature from 'components/modals/ConfirmToggleFeature'
import ConfirmRemoveFeature from 'components/modals/ConfirmRemoveFeature'
import CreateFlagModal from 'components/modals/CreateFlag'
import CreateTraitModal from 'components/modals/CreateTrait'
import TryIt from 'components/TryIt'
import CreateSegmentModal from 'components/modals/CreateSegment'
import FeatureListStore from 'common/stores/feature-list-store'
import TagFilter from 'components/tags/TagFilter'
import Tag from 'components/tags/Tag'
import { getTags } from 'common/services/useTag'
import { getStore } from 'common/store'
import TagValues from 'components/tags/TagValues'
import _data from 'common/data/base/_data'
import JSONReference from 'components/JSONReference'
import Constants from 'common/constants'
import IdentitySegmentsProvider from 'common/providers/IdentitySegmentsProvider'
import ConfigProvider from 'common/providers/ConfigProvider'
import Permission from 'common/providers/Permission'
import Icon from 'components/Icon'

const width = [200, 190, 48, 78]
const valuesEqual = (actualValue, flagValue) => {
  const nullFalseyA =
    actualValue == null ||
    actualValue === '' ||
    typeof actualValue === 'undefined'
  const nullFalseyB =
    flagValue == null || flagValue === '' || typeof flagValue === 'undefined'
  if (nullFalseyA && nullFalseyB) {
    return true
  }
  return actualValue === flagValue
}
const UserPage = class extends Component {
  static displayName = 'UserPage'

  constructor(props, context) {
    super(props, context)
    this.state = {
      preselect: Utils.fromParam().flag,
      showArchived: false,
      tags: [],
    }
  }

  getFilter = () => ({
    is_archived: this.state.showArchived,
    tags:
      !this.state.tags || !this.state.tags.length
        ? undefined
        : this.state.tags.join(','),
  })

  componentDidMount() {
    const {
      match: { params },
    } = this.props

    AppActions.getIdentity(
      this.props.match.params.environmentId,
      this.props.match.params.id,
    )
    AppActions.getIdentitySegments(
      this.props.match.params.projectId,
      this.props.match.params.id,
    )
    AppActions.getFeatures(
      this.props.match.params.projectId,
      this.props.match.params.environmentId,
      true,
      this.state.search,
      this.state.sort,
      0,
      this.getFilter(),
    )
    getTags(getStore(), {
      projectId: `${params.projectId}`,
    })
    this.getActualFlags()
    API.trackPage(Constants.pages.USER)
  }

  onSave = () => {
    this.getActualFlags()
  }

  editSegment = (segment) => {
    API.trackEvent(Constants.events.VIEW_SEGMENT)
    openModal(
      `Segment - ${segment.name}`,
      <CreateSegmentModal
        segment={segment.id}
        readOnly
        isEdit
        environmentId={this.props.match.params.environmentId}
        projectId={this.props.match.params.projectId}
      />,
      'side-modal create-segment-modal',
    )
  }

  getActualFlags = () => {
    const { environmentId, id } = this.props.match.params
    const url = `${
      Project.api
    }environments/${environmentId}/${Utils.getIdentitiesEndpoint()}/${id}/${Utils.getFeatureStatesEndpoint()}/all/`
    _data
      .get(url)
      .then((res) => {
        this.setState({ actualFlags: _.keyBy(res, (v) => v.feature.name) })
      })
      .catch(() => {})
  }

  onTraitSaved = () => {
    AppActions.getIdentitySegments(
      this.props.match.params.projectId,
      this.props.match.params.id,
    )
  }

  confirmToggle = (projectFlag, environmentFlag, cb) => {
    openModal(
      'Toggle Feature',
      <ConfirmToggleFeature
        identity={this.props.match.params.id}
        identityName={decodeURIComponent(this.props.match.params.identity)}
        environmentId={this.props.match.params.environmentId}
        projectFlag={projectFlag}
        environmentFlag={environmentFlag}
        cb={cb}
      />,
      'p-0',
    )
  }

  editFeature = (
    projectFlag,
    environmentFlag,
    identityFlag,
    multivariate_feature_state_values,
  ) => {
    history.replaceState(
      {},
      null,
      `${document.location.pathname}?flag=${projectFlag.name}`,
    )
    API.trackEvent(Constants.events.VIEW_USER_FEATURE)
    openModal(
      <span>
        Edit User Feature:{' '}
        <span className='standard-case'>{projectFlag.name}</span>
      </span>,
      <CreateFlagModal
        isEdit
        identity={this.props.match.params.id}
        identityName={decodeURIComponent(this.props.match.params.identity)}
        environmentId={this.props.match.params.environmentId}
        projectId={this.props.match.params.projectId}
        projectFlag={projectFlag}
        identityFlag={{
          ...identityFlag,
          multivariate_feature_state_values,
        }}
        environmentFlag={environmentFlag}
      />,
      'side-modal create-feature-modal overflow-y-auto',
      () => {
        history.replaceState({}, null, `${document.location.pathname}`)
      },
    )
  }

  createTrait = () => {
    API.trackEvent(Constants.events.VIEW_USER_FEATURE)
    openModal(
      'Create User Trait',
      <CreateTraitModal
        isEdit={false}
        onSave={this.onTraitSaved}
        identity={this.props.match.params.id}
        identityName={decodeURIComponent(this.props.match.params.identity)}
        environmentId={this.props.match.params.environmentId}
        projectId={this.props.match.params.projectId}
      />,
      'p-0',
    )
  }

  editTrait = (trait) => {
    API.trackEvent(Constants.events.VIEW_USER_FEATURE)
    openModal(
      'Edit User Trait',
      <CreateTraitModal
        isEdit
        {...trait}
        onSave={this.onTraitSaved}
        identity={this.props.match.params.id}
        identityName={decodeURIComponent(this.props.match.params.identity)}
        environmentId={this.props.match.params.environmentId}
        projectId={this.props.match.params.projectId}
      />,
      'p-0',
    )
  }

  confirmRemove = (projectFlag, cb, identity) => {
    openModal(
      'Reset User Feature',
      <ConfirmRemoveFeature
        identity={identity}
        environmentId={this.props.match.params.environmentId}
        projectFlag={projectFlag}
        cb={cb}
      />,
    )
  }

  removeTrait = (id, trait_key) => {
    openConfirm(
      'Delete Trait',
      <div>
        {'Are you sure you want to delete trait '}
        <strong>{trait_key}</strong>
        {' from this user?'}
      </div>,
      () =>
        AppActions.deleteIdentityTrait(
          this.props.match.params.environmentId,
          this.props.match.params.id,
          id || trait_key,
        ),
    )
  }

  filter = () => {
    AppActions.searchFeatures(
      this.props.match.params.projectId,
      this.props.match.params.environmentId,
      true,
      this.state.search,
      this.state.sort,
      0,
      this.getFilter(),
    )
  }

  render() {
    const { actualFlags } = this.state
    const { environmentId, projectId } = this.props.match.params

    const preventAddTrait = !AccountStore.getOrganisation().persist_trait_data
    return (
      <Permission
        level='environment'
        permission={Utils.getManageUserPermission()}
        id={environmentId}
      >
        {({ permission: manageUserPermission }) => (
          <Permission
            level='environment'
            permission={Utils.getManageFeaturePermission(false)}
            id={environmentId}
          >
            {({ permission }) => (
              <div className='app-container'>
                <IdentityProvider onSave={this.onSave}>
                  {(
                    {
                      environmentFlags,
                      identity,
                      identityFlags,
                      isLoading,
                      projectFlags,
                      traits,
                    },
                    { removeFlag, toggleFlag },
                  ) =>
                    isLoading &&
                    !this.state.tags.length &&
                    !this.state.tags.length &&
                    !this.state.showArchived &&
                    typeof this.state.search !== 'string' &&
                    (!identityFlags || !actualFlags || !projectFlags) ? (
                      <div className='text-center'>
                        <Loader />
                      </div>
                    ) : (
                      <div className='container'>
                        <div className='row'>
                          <div className='col-md-12'>
                            <h4>
                              {(identity && identity.identity.identifier) ||
                                this.props.match.params.id}
                            </h4>
                            <p>
                              View and manage feature states and traits for this
                              user. This will override any feature states you
                              have for your current environment for this user
                              only. Any features that are not overriden for this
                              user will fallback to the environment defaults.
                            </p>
                            <FormGroup>
                              <FormGroup>
                                <PanelSearch
                                  id='user-features-list'
                                  className='no-pad'
                                  itemHeight={70}
                                  title='Features'
                                  renderFooter={() => (
                                    <>
                                      <JSONReference
                                        showNamesButton
                                        className='mt-4 mx-2'
                                        title={'Features'}
                                        json={
                                          projectFlags &&
                                          Object.values(projectFlags)
                                        }
                                      />
                                      <JSONReference
                                        className='mx-2'
                                        title={'Environment Feature States'}
                                        json={
                                          environmentFlags &&
                                          Object.values(environmentFlags)
                                        }
                                      />
                                      <JSONReference
                                        className='mx-2'
                                        title={'Identity Feature States'}
                                        json={
                                          identityFlags &&
                                          Object.values(identityFlags)
                                        }
                                      />
                                    </>
                                  )}
                                  searchPanel={
                                    <div className='pb-2'>
                                      <TagFilter
                                        showUntagged
                                        showClearAll={
                                          (this.state.tags &&
                                            !!this.state.tags.length) ||
                                          this.state.showArchived
                                        }
                                        onClearAll={() =>
                                          this.setState(
                                            { showArchived: false, tags: [] },
                                            this.filter,
                                          )
                                        }
                                        projectId={`${projectId}`}
                                        value={this.state.tags}
                                        onChange={(tags) => {
                                          FeatureListStore.isLoading = true
                                          if (
                                            tags?.includes('') &&
                                            tags?.length > 1
                                          ) {
                                            if (!this.state.tags.includes('')) {
                                              this.setState(
                                                { tags: [''] },
                                                this.filter,
                                              )
                                            } else {
                                              this.setState(
                                                {
                                                  tags: tags?.filter(
                                                    (v) => !!v,
                                                  ),
                                                },
                                                this.filter,
                                              )
                                            }
                                          } else {
                                            this.setState({ tags }, this.filter)
                                          }
                                          AsyncStorage.setItem(
                                            `${projectId}tags`,
                                            JSON.stringify(tags),
                                          )
                                        }}
                                      >
                                        <Tag
                                          selected={this.state.showArchived}
                                          onClick={() => {
                                            FeatureListStore.isLoading = true
                                            this.setState(
                                              {
                                                showArchived:
                                                  !this.state.showArchived,
                                              },
                                              this.filter,
                                            )
                                          }}
                                          className='px-2 py-2 ml-2 mr-2'
                                          tag={{
                                            color: '#0AADDF',
                                            label: 'Archived',
                                          }}
                                        />
                                      </TagFilter>
                                    </div>
                                  }
                                  header={
                                    <Row className='table-header'>
                                      <Flex className='table-column flex-fill px-3'>
                                        Name
                                      </Flex>
                                      <div
                                        className='table-column'
                                        style={{ width: width[0] }}
                                      >
                                        Value
                                      </div>
                                      <div
                                        className='table-column'
                                        style={{ width: width[1] }}
                                      >
                                        <Switch disabled />
                                      </div>
                                      <div
                                        className='table-column'
                                        style={{ width: width[2] }}
                                      ></div>
                                    </Row>
                                  }
                                  isLoading={FeatureListStore.isLoading}
                                  onSortChange={(sort) => {
                                    this.setState({ sort }, () => {
                                      AppActions.getFeatures(
                                        this.props.match.params.projectId,
                                        this.props.match.params.environmentId,
                                        true,
                                        this.state.search,
                                        this.state.sort,
                                        0,
                                        this.getFilter(),
                                      )
                                    })
                                  }}
                                  items={projectFlags}
                                  sorting={[
                                    {
                                      default: true,
                                      label: 'Name',
                                      order: 'asc',
                                      value: 'name',
                                    },
                                    {
                                      label: 'Created Date',
                                      order: 'asc',
                                      value: 'created_date',
                                    },
                                  ]}
                                  renderRow={({ description, id, name }, i) => {
                                    const identityFlag = identityFlags[id] || {}
                                    const environmentFlag =
                                      (environmentFlags &&
                                        environmentFlags[id]) ||
                                      {}
                                    const hasUserOverride =
                                      identityFlag.identity ||
                                      identityFlag.identity_uuid
                                    const flagEnabled = hasUserOverride
                                      ? identityFlag.enabled
                                      : environmentFlag.enabled // show default value s
                                    const flagValue = hasUserOverride
                                      ? identityFlag.feature_state_value
                                      : environmentFlag.feature_state_value

                                    const actualEnabled =
                                      (actualFlags &&
                                        !!actualFlags &&
                                        actualFlags[name] &&
                                        actualFlags[name].enabled) ||
                                      false
                                    const actualValue =
                                      !!actualFlags &&
                                      actualFlags[name] &&
                                      actualFlags[name].feature_state_value
                                    const flagEnabledDifferent = hasUserOverride
                                      ? false
                                      : actualEnabled !== flagEnabled
                                    const flagValueDifferent = hasUserOverride
                                      ? false
                                      : !valuesEqual(actualValue, flagValue)
                                    const projectFlag =
                                      projectFlags &&
                                      projectFlags.find(
                                        (p) =>
                                          p.id ===
                                          (environmentFlag &&
                                            environmentFlag.feature),
                                      )
                                    const isMultiVariateOverride =
                                      flagValueDifferent &&
                                      projectFlag &&
                                      projectFlag.multivariate_options &&
                                      projectFlag.multivariate_options.find(
                                        (v) => {
                                          const value =
                                            Utils.featureStateToValue(v)
                                          return value === actualValue
                                        },
                                      )
                                    const flagDifferent =
                                      flagEnabledDifferent || flagValueDifferent
                                    const onClick = () => {
                                      if (permission) {
                                        this.editFeature(
                                          _.find(projectFlags, { id }),
                                          environmentFlags &&
                                            environmentFlags[id],
                                          (identityFlags &&
                                            identityFlags[id]) ||
                                            actualFlags[name],
                                          identityFlags &&
                                            identityFlags[id] &&
                                            identityFlags[id]
                                              .multivariate_feature_state_values,
                                        )
                                      }
                                    }

                                    if (name === this.state.preselect) {
                                      this.state.preselect = null
                                      onClick()
                                    }
                                    return (
                                      <div
                                        className={`flex-row space list-item clickable py-2 ${
                                          flagDifferent && 'flag-different'
                                        }`}
                                        key={id}
                                        data-test={`user-feature-${i}`}
                                        onClick={onClick}
                                      >
                                        <Flex className='table-column'>
                                          <Row>
                                            <Flex>
                                              <Row
                                                className='font-weight-medium'
                                                style={{
                                                  wordBreak: 'break-all',
                                                }}
                                              >
                                                <span className='me-1'>
                                                  {description ? (
                                                    <Tooltip
                                                      title={
                                                        <span>
                                                          {name}
                                                          <span
                                                            className={'ms-1'}
                                                          ></span>
                                                          <Icon name='info-outlined' />
                                                        </span>
                                                      }
                                                    >
                                                      {description}
                                                    </Tooltip>
                                                  ) : (
                                                    name
                                                  )}
                                                </span>
                                                <TagValues
                                                  projectId={`${projectId}`}
                                                  value={projectFlag.tags}
                                                />
                                              </Row>
                                              {hasUserOverride ? (
                                                <div className='list-item-subtitle'>
                                                  Overriding defaults
                                                </div>
                                              ) : flagEnabledDifferent ? (
                                                <div
                                                  data-test={`feature-override-${i}`}
                                                  className='list-item-subtitle'
                                                >
                                                  <Row>
                                                    <Flex>
                                                      {isMultiVariateOverride ? (
                                                        <span>
                                                          This flag is being
                                                          overridden by a
                                                          variation defined on
                                                          your feature, the
                                                          control value is{' '}
                                                          <strong>
                                                            {flagEnabled
                                                              ? 'on'
                                                              : 'off'}
                                                          </strong>{' '}
                                                          for this user
                                                        </span>
                                                      ) : (
                                                        <span>
                                                          This flag is being
                                                          overridden by segments
                                                          and would normally be{' '}
                                                          <strong>
                                                            {flagEnabled
                                                              ? 'on'
                                                              : 'off'}
                                                          </strong>{' '}
                                                          for this user
                                                        </span>
                                                      )}
                                                    </Flex>
                                                  </Row>
                                                </div>
                                              ) : flagValueDifferent ? (
                                                isMultiVariateOverride ? (
                                                  <div
                                                    data-test={`feature-override-${i}`}
                                                    className='list-item-subtitle'
                                                  >
                                                    <span className='flex-row'>
                                                      This feature is being
                                                      overriden by a % variation
                                                      in the environment, the
                                                      control value of this
                                                      feature is{' '}
                                                      <FeatureValue
                                                        includeEmpty
                                                        data-test={`user-feature-original-value-${i}`}
                                                        value={`${flagValue}`}
                                                      />
                                                    </span>
                                                  </div>
                                                ) : (
                                                  <div
                                                    data-test={`feature-override-${i}`}
                                                    className='list-item-subtitle'
                                                  >
                                                    <span className='flex-row'>
                                                      This feature is being
                                                      overriden by segments and
                                                      would normally be{' '}
                                                      <FeatureValue
                                                        includeEmpty
                                                        data-test={`user-feature-original-value-${i}`}
                                                        value={`${flagValue}`}
                                                      />{' '}
                                                      for this user
                                                    </span>
                                                  </div>
                                                )
                                              ) : (
                                                <div className='list-item-subtitle'>
                                                  Using environment defaults
                                                </div>
                                              )}
                                            </Flex>
                                          </Row>
                                        </Flex>
                                        <div
                                          className='table-column'
                                          style={{ width: width[0] }}
                                        >
                                          <FeatureValue
                                            data-test={`user-feature-value-${i}`}
                                            value={actualValue}
                                          />
                                        </div>
                                        <div
                                          className='table-column'
                                          style={{ width: width[1] }}
                                          onClick={(e) => {
                                            e.stopPropagation()
                                          }}
                                        >
                                          {Utils.renderWithPermission(
                                            permission,
                                            Constants.environmentPermissions(
                                              Utils.getManageFeaturePermissionDescription(
                                                false,
                                                true,
                                              ),
                                            ),
                                            <Switch
                                              disabled={!permission}
                                              data-test={`user-feature-switch-${i}${
                                                actualEnabled ? '-on' : '-off'
                                              }`}
                                              checked={actualEnabled}
                                              onChange={() =>
                                                this.confirmToggle(
                                                  _.find(projectFlags, {
                                                    id,
                                                  }),
                                                  actualFlags[name],
                                                  () => {
                                                    toggleFlag({
                                                      environmentFlag:
                                                        actualFlags[name],
                                                      environmentId:
                                                        this.props.match.params
                                                          .environmentId,
                                                      identity:
                                                        this.props.match.params
                                                          .id,
                                                      identityFlag,
                                                      projectFlag: { id },
                                                    })
                                                  },
                                                )
                                              }
                                            />,
                                          )}
                                        </div>
                                        <div
                                          className='table-column p-0'
                                          style={{ width: width[2] }}
                                          onClick={(e) => {
                                            e.stopPropagation()
                                          }}
                                        >
                                          {hasUserOverride && (
                                            <>
                                              {Utils.renderWithPermission(
                                                permission,
                                                Constants.environmentPermissions(
                                                  Utils.getManageFeaturePermissionDescription(
                                                    false,
                                                    true,
                                                  ),
                                                ),
                                                <Button
                                                  theme='text'
                                                  size='xSmall'
                                                  disabled={!permission}
                                                  onClick={() =>
                                                    this.confirmRemove(
                                                      _.find(projectFlags, {
                                                        id,
                                                      }),
                                                      () => {
                                                        removeFlag({
                                                          environmentId:
                                                            this.props.match
                                                              .params
                                                              .environmentId,
                                                          identity:
                                                            this.props.match
                                                              .params.id,
                                                          identityFlag,
                                                        })
                                                      },
                                                      identity.identity
                                                        .identifier,
                                                    )
                                                  }
                                                >
                                                  <Icon
                                                    name='refresh'
                                                    fill='#6837FC'
                                                    width={16}
                                                  />{' '}
                                                  Reset
                                                </Button>,
                                              )}
                                            </>
                                          )}
                                        </div>
                                      </div>
                                    )
                                  }}
                                  renderSearchWithNoResults
                                  renderNoResults={
                                    this.state.tags?.length ||
                                    this.state.showArchived ? (
                                      <div>No results</div>
                                    ) : (
                                      <div className='text-center m-2'>
                                        This user has no features yet. <br />
                                        When you start{' '}
                                        <Link
                                          className='dark'
                                          to={`project/${this.props.match.params.projectId}/environment/${this.props.match.params.environmentId}/features`}
                                        >
                                          creating features
                                        </Link>{' '}
                                        for your project you will set them per
                                        user here.
                                      </div>
                                    )
                                  }
                                  paging={FeatureListStore.paging}
                                  search={this.state.search}
                                  nextPage={() =>
                                    AppActions.getFeatures(
                                      this.props.match.params.projectId,
                                      this.props.match.params.environmentId,
                                      true,
                                      this.state.search,
                                      this.state.sort,
                                      FeatureListStore.paging.next,
                                      this.getFilter(),
                                    )
                                  }
                                  prevPage={() =>
                                    AppActions.getFeatures(
                                      this.props.match.params.projectId,
                                      this.props.match.params.environmentId,
                                      true,
                                      this.state.search,
                                      this.state.sort,
                                      FeatureListStore.paging.previous,
                                      this.getFilter(),
                                    )
                                  }
                                  goToPage={(page) =>
                                    AppActions.getFeatures(
                                      this.props.match.params.projectId,
                                      this.props.match.params.environmentId,
                                      true,
                                      this.state.search,
                                      this.state.sort,
                                      page,
                                      this.getFilter(),
                                    )
                                  }
                                  onChange={(e) => {
                                    this.setState(
                                      { search: Utils.safeParseEventValue(e) },
                                      () => {
                                        AppActions.searchFeatures(
                                          this.props.match.params.projectId,
                                          this.props.match.params.environmentId,
                                          true,
                                          this.state.search,
                                          this.state.sort,
                                          0,
                                          this.getFilter(),
                                        )
                                      },
                                    )
                                  }}
                                  filterRow={() => true}
                                />
                              </FormGroup>
                              {!preventAddTrait && (
                                <FormGroup>
                                  <PanelSearch
                                    id='user-traits-list'
                                    className='no-pad'
                                    itemHeight={65}
                                    title='Traits'
                                    items={traits}
                                    actionButton={
                                      <div className='ml-2'>
                                        {Utils.renderWithPermission(
                                          manageUserPermission,
                                          Constants.environmentPermissions(
                                            Utils.getManageUserPermissionDescription(),
                                          ),
                                          <Button
                                            disabled={!manageUserPermission}
                                            id='add-trait'
                                            onClick={this.createTrait}
                                            size='small'
                                          >
                                            Add new trait
                                          </Button>,
                                        )}
                                      </div>
                                    }
                                    header={
                                      <Row className='table-header'>
                                        <Flex className='table-column px-3'>
                                          Trait
                                        </Flex>
                                        <Flex className='table-column'>
                                          Value
                                        </Flex>
                                        <div
                                          className='table-column'
                                          style={{ width: '80px' }}
                                        >
                                          Remove
                                        </div>
                                      </Row>
                                    }
                                    renderRow={(
                                      { id, trait_key, trait_value },
                                      i,
                                    ) => (
                                      <Row
                                        className='list-item clickable '
                                        key={trait_key}
                                        space
                                        data-test={`user-trait-${i}`}
                                        onClick={() =>
                                          this.editTrait({
                                            id,
                                            trait_key,
                                            trait_value,
                                          })
                                        }
                                      >
                                        <Flex className='table-column px-3'>
                                          <div
                                            className={`js-trait-key-${i} font-weight-medium`}
                                          >
                                            {trait_key}
                                          </div>
                                        </Flex>
                                        <Flex className='table-column'>
                                          <FeatureValue
                                            includeEmpty
                                            data-test={`user-trait-value-${i}`}
                                            value={trait_value}
                                          />
                                        </Flex>
                                        <div
                                          className='table-column text-center'
                                          style={{ width: '80px' }}
                                          onClick={(e) => e.stopPropagation()}
                                        >
                                          {Utils.renderWithPermission(
                                            manageUserPermission,
                                            Constants.environmentPermissions(
                                              Utils.getManageUserPermissionDescription(),
                                            ),
                                            <Button
                                              id='remove-feature'
                                              className='btn btn-with-icon'
                                              type='button'
                                              disabled={!manageUserPermission}
                                              onClick={() =>
                                                this.removeTrait(id, trait_key)
                                              }
                                              data-test={`delete-user-trait-${i}`}
                                            >
                                              <Icon
                                                name='trash-2'
                                                width={20}
                                                fill='#656D7B'
                                              />
                                            </Button>,
                                          )}
                                        </div>
                                      </Row>
                                    )}
                                    renderNoResults={
                                      <Panel
                                        title='Traits'
                                        className='no-pad'
                                        action={
                                          <div>
                                            {Utils.renderWithPermission(
                                              manageUserPermission,
                                              Constants.environmentPermissions(
                                                Utils.getManageUserPermissionDescription(),
                                              ),
                                              <Button
                                                disabled={!manageUserPermission}
                                                className='mb-2'
                                                id='add-trait'
                                                onClick={this.createTrait}
                                                size='small'
                                              >
                                                Add new trait
                                              </Button>,
                                            )}
                                          </div>
                                        }
                                      >
                                        <div className='search-list'>
                                          <Row className='list-item text-muted px-3'>
                                            This user has no traits.
                                          </Row>
                                        </div>
                                      </Panel>
                                    }
                                    filterRow={({ trait_key }, search) =>
                                      trait_key.toLowerCase().indexOf(search) >
                                      -1
                                    }
                                  />
                                </FormGroup>
                              )}
                              <IdentitySegmentsProvider
                                id={this.props.match.params.id}
                              >
                                {({ segments }) =>
                                  !segments ? (
                                    <div className='text-center'>
                                      <Loader />
                                    </div>
                                  ) : (
                                    <FormGroup>
                                      <PanelSearch
                                        id='user-segments-list'
                                        className='no-pad'
                                        title='Segments'
                                        itemHeight={70}
                                        header={
                                          <Row className='table-header'>
                                            <Flex
                                              className='table-column px-3'
                                              style={{ maxWidth: '230px' }}
                                            >
                                              Name
                                            </Flex>
                                            <Flex className='table-column'>
                                              Description
                                            </Flex>
                                          </Row>
                                        }
                                        items={segments || []}
                                        renderRow={(
                                          { created_date, description, name },
                                          i,
                                        ) => (
                                          <Row
                                            onClick={() =>
                                              this.editSegment(segments[i])
                                            }
                                            className='list-item clickable'
                                            space
                                            key={i}
                                          >
                                            <Flex
                                              className=' table-column px-3'
                                              style={{ maxWidth: '230px' }}
                                            >
                                              <div
                                                onClick={() =>
                                                  this.editSegment(segments[i])
                                                }
                                              >
                                                <span
                                                  data-test={`segment-${i}-name`}
                                                  className='font-weight-medium'
                                                >
                                                  {name}
                                                </span>
                                              </div>
                                              <div className='list-item-subtitle'>
                                                Created{' '}
                                                {moment(created_date).format(
                                                  'DD/MMM/YYYY',
                                                )}
                                              </div>
                                            </Flex>
                                            <Flex className='table-column list-item-subtitle'>
                                              {description ? (
                                                <div>
                                                  {description}
                                                  <br />
                                                </div>
                                              ) : (
                                                ''
                                              )}
                                            </Flex>
                                          </Row>
                                        )}
                                        renderNoResults={
                                          <Panel
                                            title='Segments'
                                            className='no-pad'
                                          >
                                            <div className='search-list'>
                                              <Row className='list-item text-muted px-3'>
                                                This user is not a member of any
                                                segments.
                                              </Row>
                                            </div>
                                          </Panel>
                                        }
                                        filterRow={({ name }, search) =>
                                          name.toLowerCase().indexOf(search) >
                                          -1
                                        }
                                      />
                                    </FormGroup>
                                  )
                                }
                              </IdentitySegmentsProvider>
                            </FormGroup>
                          </div>
                          <div className='col-md-12 mt-2'>
                            <FormGroup>
                              <CodeHelp
                                title='Managing user traits and segments'
                                snippets={Constants.codeHelp.USER_TRAITS(
                                  this.props.match.params.environmentId,
                                  this.props.match.params.identity,
                                )}
                              />
                            </FormGroup>
                            <FormGroup>
                              <TryIt
                                title='Check to see what features and traits are coming back for this user'
                                environmentId={
                                  this.props.match.params.environmentId
                                }
                                userId={
                                  (identity && identity.identity.identifier) ||
                                  this.props.match.params.id
                                }
                              />
                            </FormGroup>
                          </div>
                        </div>
                      </div>
                    )
                  }
                </IdentityProvider>
              </div>
            )}
          </Permission>
        )}
      </Permission>
    )
  }
}

UserPage.propTypes = {}

module.exports = ConfigProvider(UserPage)
