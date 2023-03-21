import React, { Component } from 'react'
import CreateFlagModal from 'components/modals/CreateFlag'
import TryIt from 'components/TryIt'
import TagFilter from 'components/tags/TagFilter'
import Tag from 'components/tags/Tag'
import FeatureRow from 'components/FeatureRow'
import FeatureListStore from 'common/stores/feature-list-store'
import ProjectStore from 'common/stores/project-store'
import Permission from 'common/providers/Permission'
import { getTags } from 'common/services/useTag'
import { getStore } from 'common/store'
import JSONReference from 'components/JSONReference'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
const FeaturesPage = class extends Component {
  static displayName = 'FeaturesPage'

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  constructor(props, context) {
    super(props, context)
    this.state = {
      search: null,
      showArchived: false,
      sort: { label: 'Name', sortBy: 'name', sortOrder: 'asc' },
      tags: [],
    }
    ES6Component(this)
    getTags(getStore(), {
      projectId: `${this.props.match.params.projectId}`,
    })
    AppActions.getFeatures(
      this.props.match.params.projectId,
      this.props.match.params.environmentId,
      true,
      this.state.search,
      this.state.sort,
      0,
      this.getFilter(),
    )
  }

  componentWillUpdate(newProps) {
    const {
      match: { params },
    } = newProps
    const {
      match: { params: oldParams },
    } = this.props
    if (
      params.environmentId != oldParams.environmentId ||
      params.projectId != oldParams.projectId
    ) {
      AppActions.getFeatures(
        params.projectId,
        params.environmentId,
        true,
        this.state.search,
        this.state.sort,
        0,
        this.getFilter(),
      )
    }
  }

  componentDidMount = () => {
    API.trackPage(Constants.pages.FEATURES)
    const {
      match: { params },
    } = this.props
    AsyncStorage.setItem(
      'lastEnv',
      JSON.stringify({
        environmentId: params.environmentId,
        orgId: AccountStore.getOrganisation().id,
        projectId: params.projectId,
      }),
    )
  }

  newFlag = () => {
    openModal(
      'New Feature',
      <CreateFlagModal
        router={this.context.router}
        environmentId={this.props.match.params.environmentId}
        projectId={this.props.match.params.projectId}
      />,
      null,
      { className: 'side-modal fade create-feature-modal' },
    )
  }

  componentWillReceiveProps(newProps) {
    if (
      newProps.match.params.environmentId !=
      this.props.match.params.environmentId
    ) {
      AppActions.getFeatures(
        newProps.match.params.projectId,
        newProps.match.params.environmentId,
        false,
        this.state.search,
        null,
        0,
        this.getFilter(),
      )
    }
  }

  getFilter = () => ({
    is_archived: this.state.showArchived,
    tags:
      !this.state.tags || !this.state.tags.length
        ? undefined
        : this.state.tags.join(','),
  })

  onSave = () => {
    toast('Saved')
  }

  onError = (error) => {
    // Kick user back out to projects
    this.setState({ error })
    if (!error?.name && !error?.initial_value) {
      // Could not determine field level error, show generic toast.
      toast(
        'We could not create this feature, please check the name is not in use.',
      )
    }
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

  createFeaturePermission(el) {
    return (
      <Permission
        level='project'
        permission='CREATE_FEATURE'
        id={this.props.match.params.projectId}
      >
        {({ permission }) =>
          permission
            ? el(permission)
            : Utils.renderWithPermission(
                permission,
                Constants.projectPermissions('Create Feature'),
                el(permission),
              )
        }
      </Permission>
    )
  }

  render() {
    const { environmentId, projectId } = this.props.match.params
    const readOnly = Utils.getFlagsmithHasFeature('read_only_mode')
    const environment = ProjectStore.getEnvironment(environmentId)

    return (
      <div
        data-test='features-page'
        id='features-page'
        className='app-container container'
      >
        <FeatureListProvider onSave={this.onSave} onError={this.onError}>
          {({ environmentFlags, projectFlags }, { removeFlag, toggleFlag }) => {
            const isLoading = FeatureListStore.isLoading
            return (
              <div className='features-page'>
                {isLoading && (!projectFlags || !projectFlags.length) && (
                  <div className='centered-container'>
                    <Loader />
                  </div>
                )}
                {(!isLoading || (projectFlags && !!projectFlags.length)) && (
                  <div>
                    {(projectFlags && projectFlags.length) ||
                    ((this.state.showArchived ||
                      typeof this.state.search === 'string' ||
                      !!this.state.tags.length) &&
                      !isLoading) ? (
                      <div>
                        <Row>
                          <Flex>
                            <h3>Features</h3>
                            <p>
                              View and manage{' '}
                              <Tooltip
                                title={<ButtonLink>feature flags</ButtonLink>}
                                place='right'
                              >
                                {Constants.strings.FEATURE_FLAG_DESCRIPTION}
                              </Tooltip>{' '}
                              and{' '}
                              <Tooltip
                                title={<ButtonLink>remote config</ButtonLink>}
                                place='right'
                              >
                                {Constants.strings.REMOTE_CONFIG_DESCRIPTION}
                              </Tooltip>{' '}
                              for your selected environment.
                            </p>
                          </Flex>
                          <FormGroup className='float-right'>
                            {projectFlags && projectFlags.length
                              ? this.createFeaturePermission((perm) => (
                                  <div className='text-right'>
                                    <Button
                                      disabled={!perm || readOnly}
                                      data-test='show-create-feature-btn'
                                      id='show-create-feature-btn'
                                      onClick={this.newFlag}
                                    >
                                      Create Feature
                                    </Button>
                                  </div>
                                ))
                              : null}
                          </FormGroup>
                        </Row>
                        <Permission
                          level='environment'
                          permission={Utils.getManageFeaturePermission(
                            Utils.changeRequestsEnabled(
                              environment &&
                                environment.minimum_change_request_approvals,
                            ),
                          )}
                          id={this.props.match.params.environmentId}
                        >
                          {({ isLoading, permission }) => (
                            <FormGroup className='mb-4'>
                              <PanelSearch
                                className='no-pad'
                                id='features-list'
                                icon='ion-ios-rocket'
                                title='Features'
                                renderSearchWithNoResults
                                itemHeight={65}
                                isLoading={FeatureListStore.isLoading}
                                paging={FeatureListStore.paging}
                                search={this.state.search}
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
                                items={projectFlags}
                                header={
                                  <Row className='px-0 pt-0 pb-2'>
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
                                          tags.includes('') &&
                                          tags.length > 1
                                        ) {
                                          if (!this.state.tags.includes('')) {
                                            this.setState(
                                              { tags: [''] },
                                              this.filter,
                                            )
                                          } else {
                                            this.setState(
                                              { tags: tags.filter((v) => !!v) },
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
                                  </Row>
                                }
                                renderFooter={() => (
                                  <>
                                    <JSONReference
                                      className='mx-2 mt-4'
                                      showNamesButton
                                      title={'Features'}
                                      json={projectFlags}
                                    />
                                    <JSONReference
                                      className='mx-2'
                                      title={'Feature States'}
                                      json={
                                        environmentFlags &&
                                        Object.values(environmentFlags)
                                      }
                                    />
                                  </>
                                )}
                                renderRow={(projectFlag, i) => (
                                  <FeatureRow
                                    environmentFlags={environmentFlags}
                                    projectFlags={projectFlags}
                                    permission={permission}
                                    environmentId={environmentId}
                                    projectId={projectId}
                                    index={i}
                                    canDelete={permission}
                                    toggleFlag={toggleFlag}
                                    removeFlag={removeFlag}
                                    projectFlag={projectFlag}
                                  />
                                )}
                                filterRow={({ name }, search) => true}
                              />
                            </FormGroup>
                          )}
                        </Permission>
                        <FormGroup className='mt-5'>
                          <CodeHelp
                            title='1: Installing the SDK'
                            snippets={Constants.codeHelp.INSTALL}
                          />
                          <CodeHelp
                            title='2: Initialising your project'
                            snippets={Constants.codeHelp.INIT(
                              this.props.match.params.environmentId,
                              projectFlags &&
                                projectFlags[0] &&
                                projectFlags[0].name,
                            )}
                          />
                        </FormGroup>
                        <FormGroup className='pb-4'>
                          <TryIt
                            title='Test what values are being returned from the API on this environment'
                            environmentId={
                              this.props.match.params.environmentId
                            }
                          />
                        </FormGroup>
                      </div>
                    ) : (
                      <div>
                        <h3>Brilliant! Now create your features.</h3>

                        <FormGroup>
                          <Panel
                            icon='ion-ios-rocket'
                            title='1. creating a feature'
                          >
                            <p>
                              You can create two types of features for your
                              project:
                              <ul>
                                <li>
                                  <strong>Feature Flags</strong>: These allows
                                  you to toggle features on and off:
                                  <p className='faint'>
                                    EXAMPLE: You're working on a new messaging
                                    feature for your app but only show it on
                                    develop.
                                  </p>
                                </li>
                                <li>
                                  <strong>Remote configuration</strong>:
                                  configuration for a particular feature
                                  <p className='faint'>
                                    EXAMPLE: This could be absolutely anything
                                    from a font size for a website/mobile app or
                                    an environment variable for a server
                                  </p>
                                </li>
                              </ul>
                            </p>
                          </Panel>
                        </FormGroup>
                        <FormGroup>
                          <Panel
                            icon='ion-ios-settings'
                            title='2. configuring features per environment'
                          >
                            <p>
                              We've created 2 environments for you:{' '}
                              <strong>Development</strong> and{' '}
                              <strong>Production</strong>. When you create a
                              feature it makes copies of them for each
                              environment, allowing you to edit the values
                              separately. You can create more environments too
                              if you need to.
                            </p>
                          </Panel>
                        </FormGroup>

                        <FormGroup>
                          <Panel
                            icon='ion-ios-person'
                            title='3. configuring features per user'
                          >
                            <p>
                              When users login to your application, you can{' '}
                              <strong>identify</strong> them using one of our
                              SDKs, this will add them to the users page. From
                              there you can configure their features. We've
                              created an example user for you which you can see
                              in the{' '}
                              <Link
                                className='btn--link'
                                to={`/project/${projectId}/environment/${environmentId}/users`}
                              >
                                Users page
                              </Link>
                              .
                              <p className='faint'>
                                EXAMPLE: You're working on a new messaging
                                feature for your app but only show it for that
                                user.
                              </p>
                            </p>
                          </Panel>
                        </FormGroup>
                        {this.createFeaturePermission((perm) => (
                          <FormGroup className='text-center'>
                            <Button
                              disabled={!perm}
                              className='btn-lg btn-primary'
                              id='show-create-feature-btn'
                              data-test='show-create-feature-btn'
                              onClick={this.newFlag}
                            >
                              <span className='icon ion-ios-rocket' /> Create
                              your first Feature
                            </Button>
                          </FormGroup>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          }}
        </FeatureListProvider>
      </div>
    )
  }
}

FeaturesPage.propTypes = {}

module.exports = ConfigProvider(FeaturesPage)
