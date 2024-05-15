import React, { Component } from 'react'
import ConfirmToggleFeature from 'components/modals/ConfirmToggleFeature'
import CreateFlagModal from 'components/modals/CreateFlag'
import CreateTraitModal from 'components/modals/CreateTrait'
import TryIt from 'components/TryIt'
import CreateSegmentModal from 'components/modals/CreateSegment'
import FeatureListStore from 'common/stores/feature-list-store'
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
import FeatureValue from 'components/FeatureValue'
import PageTitle from 'components/PageTitle'
import TableTagFilter from 'components/tables/TableTagFilter'
import TableSearchFilter from 'components/tables/TableSearchFilter'
import TableFilterOptions from 'components/tables/TableFilterOptions'
import TableSortFilter from 'components/tables/TableSortFilter'
import { getViewMode, setViewMode } from 'common/useViewMode'
import classNames from 'classnames'
import IdentifierString from 'components/IdentifierString'
import Button from 'components/base/forms/Button'
import { removeUserOverride } from 'components/RemoveUserOverride'
import TableOwnerFilter from 'components/tables/TableOwnerFilter'
import TableGroupsFilter from 'components/tables/TableGroupsFilter'
import TableValueFilter from 'components/tables/TableValueFilter'
import Format from 'common/utils/format'
import InfoMessage from 'components/InfoMessage'
const width = [200, 48, 78]
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

    const params = Utils.fromParam()
    this.state = {
      group_owners:
        typeof params.group_owners === 'string'
          ? params.group_owners.split(',').map((v) => parseInt(v))
          : [],
      is_enabled:
        params.is_enabled === 'true'
          ? true
          : params.is_enabled === 'false'
          ? false
          : null,
      loadedOnce: false,
      owners:
        typeof params.owners === 'string'
          ? params.owners.split(',').map((v) => parseInt(v))
          : [],
      page: params.page ? parseInt(params.page) - 1 : 1,
      preselect: Utils.fromParam().flag,
      search: params.search || null,
      showArchived: params.is_archived === 'true',
      sort: {
        label: Format.camelCase(params.sortBy || 'Name'),
        sortBy: params.sortBy || 'name',
        sortOrder: params.sortOrder || 'asc',
      },
      tag_strategy: params.tag_strategy || 'INTERSECTION',
      tags:
        typeof params.tags === 'string'
          ? params.tags.split(',').map((v) => parseInt(v))
          : [],
      value_search:
        typeof params.value_search === 'string' ? params.value_search : '',
    }
  }

  getFilter = () => ({
    group_owners: this.state.group_owners?.length
      ? this.state.group_owners
      : undefined,
    is_archived: this.state.showArchived,
    is_enabled:
      this.state.is_enabled === null ? undefined : this.state.is_enabled,
    owners: this.state.owners?.length ? this.state.owners : undefined,
    tag_strategy: this.state.tag_strategy,
    tags:
      !this.state.tags || !this.state.tags.length
        ? undefined
        : this.state.tags.join(','),
    value_search: this.state.value_search ? this.state.value_search : undefined,
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
        <Row>
          Edit User Feature:{' '}
          <span className='standard-case'>{projectFlag.name}</span>
          <Button
            onClick={() => {
              Utils.copyFeatureName(projectFlag.name)
            }}
            theme='icon'
            className='ms-2'
          >
            <Icon name='copy' />
          </Button>
        </Row>
      </span>,
      <CreateFlagModal
        history={this.props.router.history}
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

  removeTrait = (id, trait_key) => {
    openConfirm({
      body: (
        <div>
          {'Are you sure you want to delete trait '}
          <strong>{trait_key}</strong>
          {
            ' from this user? Traits can be re-added here or via one of our SDKs.'
          }
        </div>
      ),
      destructive: true,
      onYes: () =>
        AppActions.deleteIdentityTrait(
          this.props.match.params.environmentId,
          this.props.match.params.id,
          id || trait_key,
        ),
      title: 'Delete Trait',
      yesText: 'Confirm',
    })
  }
  getURLParams = () => ({
    ...this.getFilter(),
    group_owners: (this.state.group_owners || [])?.join(',') || undefined,
    owners: (this.state.owners || [])?.join(',') || undefined,
    page: this.state.page || 1,
    search: this.state.search || '',
    sortBy: this.state.sort.sortBy,
    sortOrder: this.state.sort.sortOrder,
    tags: (this.state.tags || [])?.join(',') || undefined,
  })

  filter = () => {
    const currentParams = Utils.fromParam()
    if (!currentParams.flag) {
      // don't replace page if we are currently viewing a feature
      this.props.router.history.replace(
        `${document.location.pathname}?${Utils.toParam(this.getURLParams())}`,
      )
    }
    AppActions.searchFeatures(
      this.props.match.params.projectId,
      this.props.match.params.environmentId,
      true,
      this.state.search,
      this.state.sort,
      this.getFilter(),
    )
  }

  render() {
    const { actualFlags } = this.state
    const { environmentId, projectId } = this.props.match.params
    const preventAddTrait = !AccountStore.getOrganisation().persist_trait_data
    return (
      <div className='app-container container'>
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
                <div>
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
                        <>
                          <PageTitle
                            title={
                              <IdentifierString
                                value={
                                  (identity && identity.identity.identifier) ||
                                  this.props.match.params.id
                                }
                              />
                            }
                          >
                            View and manage feature states and traits for this
                            user.
                            <br />
                          </PageTitle>
                          <div className='row'>
                            <div className='col-md-12'>
                              <FormGroup>
                                <FormGroup>
                                  <PanelSearch
                                    id='user-features-list'
                                    className='no-pad overflow-visible'
                                    itemHeight={70}
                                    title={
                                      <div>
                                        Features
                                        <div className='fw-normal mt-2 fs-medium'>
                                          <InfoMessage>
                                            Overriding features here will take
                                            priority over any segment override.
                                            Any features that are not overridden
                                            for this user will fallback to any
                                            segment overrides or the environment
                                            defaults.
                                          </InfoMessage>
                                        </div>
                                      </div>
                                    }
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
                                    header={
                                      <Row className='table-header'>
                                        <div className='table-column flex-row flex-fill'>
                                          <TableSearchFilter
                                            onChange={(e) => {
                                              FeatureListStore.isLoading = true
                                              this.setState(
                                                {
                                                  search:
                                                    Utils.safeParseEventValue(
                                                      e,
                                                    ),
                                                },
                                                this.filter,
                                              )
                                            }}
                                            value={this.state.search}
                                          />
                                          <Row className='flex-fill justify-content-end'>
                                            <TableTagFilter
                                              useLocalStorage
                                              projectId={projectId}
                                              className='me-4'
                                              title='Tags'
                                              value={this.state.tags}
                                              tagStrategy={
                                                this.state.tag_strategy
                                              }
                                              onChangeStrategy={(
                                                tag_strategy,
                                              ) => {
                                                this.setState(
                                                  {
                                                    tag_strategy,
                                                  },
                                                  this.filter,
                                                )
                                              }}
                                              isLoading={
                                                FeatureListStore.isLoading
                                              }
                                              onToggleArchived={(value) => {
                                                if (
                                                  value !==
                                                  this.state.showArchived
                                                ) {
                                                  FeatureListStore.isLoading = true
                                                  this.setState(
                                                    {
                                                      showArchived:
                                                        !this.state
                                                          .showArchived,
                                                    },
                                                    this.filter,
                                                  )
                                                }
                                              }}
                                              showArchived={
                                                this.state.showArchived
                                              }
                                              onClearAll={() => {
                                                FeatureListStore.isLoading = true
                                                this.setState(
                                                  {
                                                    showArchived: false,
                                                    tags: [],
                                                  },
                                                  this.filter,
                                                )
                                              }}
                                              onChange={(tags) => {
                                                FeatureListStore.isLoading = true
                                                if (
                                                  tags.includes('') &&
                                                  tags.length > 1
                                                ) {
                                                  if (
                                                    !this.state.tags.includes(
                                                      '',
                                                    )
                                                  ) {
                                                    this.setState(
                                                      { tags: [''] },
                                                      this.filter,
                                                    )
                                                  } else {
                                                    this.setState(
                                                      {
                                                        tags: tags.filter(
                                                          (v) => !!v,
                                                        ),
                                                      },
                                                      this.filter,
                                                    )
                                                  }
                                                } else {
                                                  this.setState(
                                                    { tags },
                                                    this.filter,
                                                  )
                                                }
                                                AsyncStorage.setItem(
                                                  `${projectId}tags`,
                                                  JSON.stringify(tags),
                                                )
                                              }}
                                            />
                                            <TableValueFilter
                                              className='me-4'
                                              useLocalStorage
                                              value={{
                                                enabled: this.state.is_enabled,
                                                valueSearch:
                                                  this.state.value_search,
                                              }}
                                              onChange={({
                                                enabled,
                                                valueSearch,
                                              }) => {
                                                this.setState(
                                                  {
                                                    is_enabled: enabled,
                                                    value_search: valueSearch,
                                                  },
                                                  this.filter,
                                                )
                                              }}
                                            />
                                            <TableOwnerFilter
                                              title={'Owners'}
                                              className={'me-4'}
                                              useLocalStorage
                                              value={this.state.owners}
                                              onChange={(owners) => {
                                                FeatureListStore.isLoading = true
                                                this.setState(
                                                  {
                                                    owners: owners,
                                                  },
                                                  this.filter,
                                                )
                                              }}
                                            />
                                            <TableGroupsFilter
                                              title={'Groups'}
                                              className={'me-4'}
                                              projectId={projectId}
                                              orgId={
                                                AccountStore.getOrganisation()
                                                  ?.id
                                              }
                                              useLocalStorage
                                              value={this.state.group_owners}
                                              onChange={(group_owners) => {
                                                FeatureListStore.isLoading = true
                                                this.setState(
                                                  {
                                                    group_owners: group_owners,
                                                  },
                                                  this.filter,
                                                )
                                              }}
                                            />
                                            <TableFilterOptions
                                              title={'View'}
                                              className={'me-4'}
                                              value={getViewMode()}
                                              onChange={setViewMode}
                                              options={[
                                                {
                                                  label: 'Default',
                                                  value: 'default',
                                                },
                                                {
                                                  label: 'Compact',
                                                  value: 'compact',
                                                },
                                              ]}
                                            />
                                            <TableSortFilter
                                              value={this.state.sort}
                                              isLoading={
                                                FeatureListStore.isLoading
                                              }
                                              options={[
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
                                              onChange={(sort) => {
                                                FeatureListStore.isLoading = true
                                                this.setState(
                                                  { sort },
                                                  this.filter,
                                                )
                                              }}
                                            />
                                          </Row>
                                        </div>
                                      </Row>
                                    }
                                    isLoading={FeatureListStore.isLoading}
                                    items={projectFlags}
                                    renderRow={(
                                      { description, id, name },
                                      i,
                                    ) => {
                                      const identityFlag =
                                        identityFlags[id] || {}
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
                                      const flagEnabledDifferent =
                                        hasUserOverride
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
                                        flagEnabledDifferent ||
                                        flagValueDifferent
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
                                      const isCompact =
                                        getViewMode() === 'compact'
                                      if (
                                        name === this.state.preselect &&
                                        actualFlags
                                      ) {
                                        this.state.preselect = null
                                        onClick()
                                      }
                                      return (
                                        <div
                                          className={classNames(
                                            `flex-row space list-item clickable py-2 ${
                                              flagDifferent && 'flag-different'
                                            }`,
                                            {
                                              'list-item-xs':
                                                isCompact &&
                                                !flagEnabledDifferent &&
                                                !flagValueDifferent,
                                            },
                                          )}
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
                                                    alignItems: 'start',
                                                    lineHeight: 1,
                                                    rowGap: 4,
                                                    wordBreak: 'break-all',
                                                  }}
                                                >
                                                  <Row>
                                                    <span>
                                                      {description ? (
                                                        <Tooltip
                                                          title={
                                                            <span>{name}</span>
                                                          }
                                                        >
                                                          {description}
                                                        </Tooltip>
                                                      ) : (
                                                        name
                                                      )}
                                                    </span>
                                                    <Button
                                                      onClick={(e) => {
                                                        e?.stopPropagation()?.()
                                                        e?.currentTarget?.blur?.()
                                                        Utils.copyFeatureName(
                                                          projectFlag.name,
                                                        )
                                                      }}
                                                      theme='icon'
                                                      className='ms-2 me-2'
                                                    >
                                                      <Icon name='copy' />
                                                    </Button>
                                                  </Row>

                                                  <TagValues
                                                    projectId={`${projectId}`}
                                                    value={projectFlag.tags}
                                                  />
                                                </Row>
                                                {hasUserOverride ? (
                                                  <div className='list-item-subtitle mt-1'>
                                                    Overriding defaults
                                                  </div>
                                                ) : flagEnabledDifferent ? (
                                                  <div
                                                    data-test={`feature-override-${i}`}
                                                    className='list-item-subtitle mt-1'
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
                                                            overridden by
                                                            segments and would
                                                            normally be{' '}
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
                                                      className='list-item-subtitle mt-1'
                                                    >
                                                      <span className='flex-row'>
                                                        This feature is being
                                                        overriden by a %
                                                        variation in the
                                                        environment, the control
                                                        value of this feature is{' '}
                                                        <FeatureValue
                                                          className='ml-1 chip--xs'
                                                          includeEmpty
                                                          data-test={`user-feature-original-value-${i}`}
                                                          value={`${flagValue}`}
                                                        />
                                                      </span>
                                                    </div>
                                                  ) : (
                                                    <div
                                                      data-test={`feature-override-${i}`}
                                                      className='list-item-subtitle mt-1'
                                                    >
                                                      <span className='flex-row'>
                                                        This feature is being
                                                        overriden by segments
                                                        and would normally be{' '}
                                                        <FeatureValue
                                                          className='ml-1 chip--xs'
                                                          includeEmpty
                                                          data-test={`user-feature-original-value-${i}`}
                                                          value={`${flagValue}`}
                                                        />{' '}
                                                        for this user
                                                      </span>
                                                    </div>
                                                  )
                                                ) : (
                                                  getViewMode() ===
                                                    'default' && (
                                                    <div className='list-item-subtitle mt-1'>
                                                      Using environment defaults
                                                    </div>
                                                  )
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
                                                          this.props.match
                                                            .params
                                                            .environmentId,
                                                        identity:
                                                          this.props.match
                                                            .params.id,
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
                                                    onClick={() => {
                                                      const projectFlag =
                                                        _.find(projectFlags, {
                                                          id,
                                                        })
                                                      const environmentId =
                                                        this.props.match.params
                                                          .environmentId

                                                      removeUserOverride({
                                                        environmentId,
                                                        identifier:
                                                          identity.identity
                                                            .identifier,
                                                        identity:
                                                          this.props.match
                                                            .params.id,
                                                        identityFlag,
                                                        projectFlag,
                                                      })
                                                    }}
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
                                                  this.removeTrait(
                                                    id,
                                                    trait_key,
                                                  )
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
                                                  disabled={
                                                    !manageUserPermission
                                                  }
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
                                        trait_key
                                          .toLowerCase()
                                          .indexOf(search) > -1
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
                                                    this.editSegment(
                                                      segments[i],
                                                    )
                                                  }
                                                >
                                                  <span
                                                    data-test={`segment-${i}-name`}
                                                    className='font-weight-medium'
                                                  >
                                                    {name}
                                                  </span>
                                                </div>
                                                <div className='list-item-subtitle mt-1'>
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
                                                  This user is not a member of
                                                  any segments.
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
                                    (identity &&
                                      identity.identity.identifier) ||
                                    this.props.match.params.id
                                  }
                                />
                              </FormGroup>
                            </div>
                          </div>
                        </>
                      )
                    }
                  </IdentityProvider>
                </div>
              )}
            </Permission>
          )}
        </Permission>
      </div>
    )
  }
}

UserPage.propTypes = {}

module.exports = ConfigProvider(UserPage)
