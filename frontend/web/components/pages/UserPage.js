import React, { Component } from 'react'
import CreateTraitModal from 'components/modals/CreateTrait'
import TryIt from 'components/TryIt'
import CreateSegmentModal from 'components/modals/CreateSegment'
import FeatureListStore from 'common/stores/feature-list-store'
import TagFilter from 'components/tags/TagFilter'
import Tag from 'components/tags/Tag'
import { getTags } from 'common/services/useTag'
import { getStore } from 'common/store'
import _data from 'common/data/base/_data'
import JSONReference from 'components/JSONReference'
import Constants from 'common/constants'
import IdentitySegmentsProvider from 'common/providers/IdentitySegmentsProvider'
import ConfigProvider from 'common/providers/ConfigProvider'
import Permission from 'common/providers/Permission'
import IdentityStateRow from 'components/IdentityStateRow'
import FeatureValue from 'components/FeatureValue'
const UserPage = class extends Component {
  static displayName = 'UserPage'

  constructor(props, context) {
    super(props, context)
    this.state = {
      preselect: Utils.fromParam().flag,
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
      null,
      { className: 'fade side-modal create-segment-modal' },
    )
  }

  getActualFlags = () => {
    const { environmentId, id } = this.props.match.params
    if (Utils.getFlagsmithHasFeature('use_admin_identity_featurestates')) {
      const url = `${
        Project.api
      }environments/${environmentId}/${Utils.getIdentitiesEndpoint()}/${id}/${Utils.getFeatureStatesEndpoint()}/all/`
      _data
        .get(url)
        .then((res) => {
          this.setState({ actualFlags: _.keyBy(res, (v) => v.feature.name) })
        })
        .catch(() => {})
    } else {
      const url = `${Utils.getSDKEndpoint()}identities/?identifier=${
        this.props.match.params.identity
      }`
      fetch(url, {
        headers: { 'X-Environment-Key': this.props.match.params.environmentId },
      })
        .then((res) => res.json())
        .then((res) => {
          this.setState({
            actualFlags: _.keyBy(res.flags, (v) => v.feature.name),
          })
        })
        .catch(() => {})
    }
  }

  onTraitSaved = () => {
    AppActions.getIdentitySegments(
      this.props.match.params.projectId,
      this.props.match.params.id,
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
    )
  }

  removeTrait = (id, trait_key) => {
    openConfirm(
      <h3>Delete Trait</h3>,
      <p>
        {'Are you sure you want to delete trait '}
        <strong>{trait_key}</strong>
        {' from this user?'}
      </p>,
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
          <div className='app-container'>
            <IdentityProvider>
              {({
                environmentFlags,
                identity,
                identityFlags,
                isLoading,
                projectFlags,
                traits,
              }) =>
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
                        <h3>
                          {(identity && identity.identity.identifier) ||
                            this.props.match.params.id}
                        </h3>
                        <p>
                          View and manage feature states and traits for this
                          user. This will override any feature states you have
                          for your current environment for this user only. Any
                          features that are not overriden for this user will
                          fallback to the environment defaults.
                        </p>
                        <FormGroup>
                          <FormGroup>
                            <PanelSearch
                              id='user-features-list'
                              className='no-pad'
                              itemHeight={70}
                              icon='ion-ios-rocket'
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
                              header={
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
                                              tags: tags?.filter((v) => !!v),
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
                                      tag={{ label: 'Archived' }}
                                    />
                                  </TagFilter>
                                </div>
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
                              renderRow={({ id, name }, i) => {
                                const onClick = (projectFlag) => {
                                  this.state.preselect = null
                                  history.replaceState(
                                    {},
                                    null,
                                    `${document.location.pathname}?flag=${projectFlag.name}`,
                                  )
                                }
                                return (
                                  <IdentityStateRow
                                    actualFlags={actualFlags}
                                    environmentFlags={environmentFlags}
                                    environmentId={environmentId}
                                    featureId={id}
                                    featureName={name}
                                    identityFlags={identityFlags}
                                    identityId={this.props.match.params.id}
                                    identityName={decodeURIComponent(
                                      this.props.match.params.identity,
                                    )}
                                    onClick={onClick}
                                    onSave={this.onSave}
                                    projectFlags={projectFlags}
                                    projectId={projectId}
                                  />
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
                                    for your project you will set them per user
                                    here.
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
                                icon='ion-ios-person'
                                itemHeight={65}
                                title='Traits'
                                items={traits}
                                renderFooter={() => (
                                  <FormGroup className='text-center mb-2'>
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
                                      >
                                        Add new trait
                                      </Button>,
                                    )}
                                  </FormGroup>
                                )}
                                renderRow={(
                                  { id, trait_key, trait_value },
                                  i,
                                ) => (
                                  <Row
                                    className='list-item clickable py-2'
                                    key={trait_key}
                                    space
                                    data-test={`user-trait-${i}`}
                                  >
                                    <div
                                      onClick={() =>
                                        this.editTrait({
                                          id,
                                          trait_key,
                                          trait_value,
                                        })
                                      }
                                      className='flex flex-1'
                                    >
                                      <Row>
                                        <ButtonLink
                                          className={`js-trait-key-${i}`}
                                          href='#'
                                        >
                                          {trait_key}
                                        </ButtonLink>
                                      </Row>
                                    </div>
                                    <Row>
                                      <Column>
                                        <FeatureValue
                                          includeEmpty
                                          data-test={`user-trait-value-${i}`}
                                          value={trait_value}
                                        />
                                      </Column>
                                      <Column>
                                        {Utils.renderWithPermission(
                                          manageUserPermission,
                                          Constants.environmentPermissions(
                                            Utils.getManageUserPermissionDescription(),
                                          ),
                                          <button
                                            id='remove-feature'
                                            className='btn btn--with-icon'
                                            type='button'
                                            disabled={!manageUserPermission}
                                            onClick={() =>
                                              this.removeTrait(id, trait_key)
                                            }
                                            data-test={`delete-user-trait-${i}`}
                                          >
                                            <RemoveIcon />
                                          </button>,
                                        )}
                                      </Column>
                                    </Row>
                                  </Row>
                                )}
                                renderNoResults={
                                  <Panel icon='ion-ios-person' title='Traits'>
                                    <div className='text-center'>
                                      This user has no traits.
                                      <FormGroup className='text-center mb-0 mt-2'>
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
                                          >
                                            Add new trait
                                          </Button>,
                                        )}
                                      </FormGroup>
                                    </div>
                                  </Panel>
                                }
                                filterRow={({ trait_key }, search) =>
                                  trait_key.toLowerCase().indexOf(search) > -1
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
                                    icon='ion-ios-globe'
                                    title='Segments'
                                    itemHeight={70}
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
                                        <div className='flex flex-1'>
                                          <Row>
                                            <ButtonLink
                                              onClick={() =>
                                                this.editSegment(segments[i])
                                              }
                                            >
                                              <span
                                                data-test={`segment-${i}-name`}
                                                className='bold-link'
                                              >
                                                {name}
                                              </span>
                                            </ButtonLink>
                                          </Row>
                                          <div className='list-item-footer faint mt-2'>
                                            {description ? (
                                              <div>
                                                {description}
                                                <br />
                                              </div>
                                            ) : (
                                              ''
                                            )}
                                            Created{' '}
                                            {moment(created_date).format(
                                              'DD/MMM/YYYY',
                                            )}
                                          </div>
                                        </div>
                                      </Row>
                                    )}
                                    renderNoResults={
                                      <Panel
                                        icon='ion-ios-globe'
                                        title='Segments'
                                      >
                                        <div>
                                          This user is not a member of any
                                          segments.
                                        </div>
                                      </Panel>
                                    }
                                    filterRow={({ name }, search) =>
                                      name.toLowerCase().indexOf(search) > -1
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
    )
  }
}

UserPage.propTypes = {}

module.exports = ConfigProvider(UserPage)
