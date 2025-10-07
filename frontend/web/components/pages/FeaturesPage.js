import React, { Component } from 'react'
import CreateFlagModal from 'components/modals/CreateFlag'
import TryIt from 'components/TryIt'
import FeatureRow from 'components/feature-summary/FeatureRow'
import FeatureListStore from 'common/stores/feature-list-store'
import ProjectStore from 'common/stores/project-store'
import Permission from 'common/providers/Permission'
import JSONReference from 'components/JSONReference'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
import PageTitle from 'components/PageTitle'
import { rocket } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'
import EnvironmentDocumentCodeHelp from 'components/EnvironmentDocumentCodeHelp'
import classNames from 'classnames'
import Button from 'components/base/forms/Button'
import EnvironmentMetricsList from 'components/metrics/EnvironmentMetricsList'
import { withRouter } from 'react-router-dom'
import { useRouteContext } from 'components/providers/RouteContext'
import FeatureFilters, {
  getFiltersFromURLParams,
  getServerFilter,
  getURLParamsFromFilters,
} from 'components/feature-page/FeatureFilters'

const FeaturesPage = class extends Component {
  static displayName = 'FeaturesPage'

  constructor(props) {
    super(props)
    this.state = {
      filters: getFiltersFromURLParams(Utils.fromParam()),
      forceMetricsRefetch: false,
      loadedOnce: false,
    }
    ES6Component(this)
    this.projectId = this.props.routeContext.projectId
    const { filters } = this.state
    AppActions.getFeatures(
      this.projectId,
      this.props.match.params.environmentId,
      true,
      filters.search,
      filters.sort,
      filters.page,
      getServerFilter(filters),
    )
  }

  componentDidUpdate(prevProps) {
    const {
      match: { params },
    } = this.props
    const {
      match: { params: oldParams },
    } = prevProps
    if (
      params.environmentId !== oldParams.environmentId ||
      params.projectId !== oldParams.projectId
    ) {
      this.setState({ loadedOnce: false }, () => this.filter())
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
        orgId: AccountStore.getOrganisation()?.id,
        projectId: params.projectId,
      }),
    )
  }

  newFlag = () => {
    openModal(
      'New Feature',
      <CreateFlagModal
        history={this.props.history}
        environmentId={this.props.match.params.environmentId}
        projectId={this.projectId}
      />,
      'side-modal create-feature-modal',
    )
  }

  toggleForceMetricsRefetch = () => {
    this.setState((prevState) => ({
      forceMetricsRefetch: !prevState.forceMetricsRefetch,
    }))
  }

  onError = (error) => {
    if (!error?.name && !error?.initial_value) {
      toast(
        error.project ||
          'We could not create this feature, please check the name is not in use.',
        'danger',
      )
    }
  }

  filter = (page) => {
    const currentParams = Utils.fromParam()
    const nextFilters =
      typeof page === 'number'
        ? { ...this.state.filters, page }
        : this.state.filters
    this.setState({ filters: nextFilters }, () => {
      const f = this.state.filters
      if (!currentParams.feature) {
        this.props.history.replace(
          `${document.location.pathname}?${Utils.toParam(
            getURLParamsFromFilters(this.state.filters),
          )}`,
        )
      }
      if (page) {
        AppActions.getFeatures(
          this.projectId,
          this.props.match.params.environmentId,
          true,
          f.search,
          f.sort,
          page,
          getServerFilter(f),
        )
      } else {
        AppActions.searchFeatures(
          this.projectId,
          this.props.match.params.environmentId,
          true,
          f.search,
          f.sort,
          getServerFilter(f),
        )
      }
    })
  }

  createFeaturePermission(el) {
    return (
      <Permission
        level='project'
        permission='CREATE_FEATURE'
        id={this.projectId}
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
    const environmentMetricsEnabled = Utils.getFlagsmithHasFeature(
      'environment_metrics',
    )

    const environment = ProjectStore.getEnvironment(environmentId)

    return (
      <div
        data-test='features-page'
        id='features-page'
        className='app-container container'
      >
        <FeatureListProvider
          onRemove={(feature) => {
            this.toggleForceMetricsRefetch()
            return toast(
              <div>
                Removed feature: <strong>{feature.name}</strong>
              </div>,
            )
          }}
          onSave={this.toggleForceMetricsRefetch}
          onError={this.onError}
        >
          {(
            {
              environmentFlags,
              maxFeaturesAllowed,
              projectFlags,
              totalFeatures,
            },
            { removeFlag, toggleFlag },
          ) => {
            const isLoading = !FeatureListStore.hasLoaded
            const isSaving = FeatureListStore.isSaving
            const featureLimitAlert = Utils.calculateRemainingLimitsPercentage(
              totalFeatures,
              maxFeaturesAllowed,
            )

            if (FeatureListStore.hasLoaded && !this.state.loadedOnce) {
              this.state.loadedOnce = true
            }

            return (
              <div className='features-page'>
                {(isLoading || !this.state.loadedOnce) &&
                  (!projectFlags || !projectFlags.length) && (
                    <div className='centered-container'>
                      <Loader />
                    </div>
                  )}
                {(!isLoading || this.state.loadedOnce) && (
                  <div>
                    {this.state.loadedOnce ||
                    ((this.state.filters.is_archived ||
                      typeof this.state.filters.search === 'string' ||
                      !!this.state.filters.tags.length) &&
                      !isLoading) ? (
                      <div>
                        {featureLimitAlert.percentage &&
                          Utils.displayLimitAlert(
                            'features',
                            featureLimitAlert.percentage,
                          )}
                        {environmentMetricsEnabled && (
                          <EnvironmentMetricsList
                            environmentApiKey={environment?.api_key}
                            forceRefetch={this.state.forceMetricsRefetch}
                            projectId={projectId}
                          />
                        )}
                        <PageTitle
                          title={'Features'}
                          cta={
                            <>
                              {this.state.loadedOnce ||
                              this.state.filters.is_archived ||
                              this.state.filters.tags?.length
                                ? this.createFeaturePermission((perm) => (
                                    <Button
                                      disabled={
                                        !perm ||
                                        readOnly ||
                                        featureLimitAlert.percentage >= 100
                                      }
                                      className='w-100'
                                      data-test='show-create-feature-btn'
                                      id='show-create-feature-btn'
                                      onClick={this.newFlag}
                                    >
                                      Create Feature
                                    </Button>
                                  ))
                                : null}
                            </>
                          }
                        >
                          View and manage{' '}
                          <Tooltip
                            title={
                              <Button className='fw-normal' theme='text'>
                                feature flags
                              </Button>
                            }
                            place='right'
                          >
                            {Constants.strings.FEATURE_FLAG_DESCRIPTION}
                          </Tooltip>{' '}
                          and{' '}
                          <Tooltip
                            title={
                              <Button className='fw-normal' theme='text'>
                                remote config
                              </Button>
                            }
                            place='right'
                          >
                            {Constants.strings.REMOTE_CONFIG_DESCRIPTION}
                          </Tooltip>{' '}
                          for your selected environment.
                        </PageTitle>
                        <FormGroup
                          className={classNames('mb-4', {
                            'opacity-50': isSaving,
                          })}
                        >
                          <PanelSearch
                            className='no-pad overflow-visible'
                            id='features-list'
                            renderSearchWithNoResults
                            itemHeight={65}
                            isLoading={FeatureListStore.isLoading}
                            paging={FeatureListStore.paging}
                            header={
                              <FeatureFilters
                                value={this.state.filters}
                                projectId={projectId}
                                orgId={AccountStore.getOrganisation()?.id}
                                isLoading={FeatureListStore.isLoading}
                                onChange={(next) => {
                                  FeatureListStore.isLoading = true
                                  this.setState({ filters: next }, this.filter)
                                }}
                              />
                            }
                            nextPage={() =>
                              this.filter(FeatureListStore.paging.next)
                            }
                            prevPage={() =>
                              this.filter(FeatureListStore.paging.previous)
                            }
                            goToPage={(page) => this.filter(page)}
                            items={projectFlags?.filter((v) => !v.ignore)}
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
                              <Permission
                                level='environment'
                                tags={projectFlag.tags}
                                permission={Utils.getManageFeaturePermission(
                                  Utils.changeRequestsEnabled(
                                    environment &&
                                      environment.minimum_change_request_approvals,
                                  ),
                                )}
                                id={this.props.match.params.environmentId}
                              >
                                {({ permission }) => (
                                  <FeatureRow
                                    environmentFlags={environmentFlags}
                                    permission={permission}
                                    history={this.props.history}
                                    environmentId={environmentId}
                                    projectId={projectId}
                                    index={i}
                                    canDelete={permission}
                                    toggleFlag={toggleFlag}
                                    removeFlag={removeFlag}
                                    projectFlag={projectFlag}
                                  />
                                )}
                              </Permission>
                            )}
                          />
                        </FormGroup>
                        <FormGroup className='mt-5'>
                          <CodeHelp
                            title='1: Installing the SDK'
                            snippets={Constants.codeHelp.INSTALL}
                          />
                          <CodeHelp
                            title='2: Initialising your project'
                            snippets={Constants.codeHelp.INIT(
                              this.props.match.params.environmentId,
                              projectFlags?.[0]?.name,
                            )}
                          />
                          <EnvironmentDocumentCodeHelp
                            title='3: Providing feature defaults and support offline'
                            projectId={projectId}
                            environmentId={
                              this.props.match.params.environmentId
                            }
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
                      !isLoading &&
                      this.state.loadedOnce && (
                        <div>
                          <h3>Brilliant! Now create your features.</h3>
                          <FormGroup>
                            <Panel
                              icon='ion-ios-settings'
                              title='1. configuring features per environment'
                            >
                              <p>
                                We've created 2 Environments for you:{' '}
                                <strong>Development</strong> and{' '}
                                <strong>Production</strong>. When you create a
                                Feature it makes copies of them for each
                                Environment, allowing you to edit the values
                                separately. You can create more Environments too
                                if you need to.
                              </p>
                            </Panel>
                          </FormGroup>
                          <FormGroup>
                            <Panel
                              icon='ion-ios-rocket'
                              title='2. creating a feature'
                            >
                              <p>
                                Features in Flagsmith are made up of two
                                different data types:
                                <ul>
                                  <li>
                                    <strong>Booleans</strong>: These allows you
                                    to toggle features on and off:
                                    <p className='faint'>
                                      EXAMPLE: You're working on a new messaging
                                      feature for your app but only want to show
                                      it in your Development Environment.
                                    </p>
                                  </li>
                                  <li>
                                    <strong>String Values</strong>:
                                    configuration for a particular feature
                                    <p className='faint'>
                                      EXAMPLE: This could be absolutely anything
                                      from a font size for a website/mobile app
                                      or an environment variable for a server
                                    </p>
                                  </li>
                                </ul>
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
                                <strong>Identify</strong> them using one of our
                                SDKs, this will add them to the Identities page.
                                From there you can configure their Features.
                                We've created an example user for you which you
                                can see in the{' '}
                                <Link
                                  className='btn-link'
                                  to={`/project/${projectId}/environment/${environmentId}/users`}
                                >
                                  Identities page
                                </Link>
                                .
                                <p className='faint'>
                                  EXAMPLE: You're working on a new messaging
                                  feature for your app but only want to show it
                                  for that Identity.
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
                                <div className='flex-row justify-content-center'>
                                  <IonIcon
                                    className='me-1'
                                    icon={rocket}
                                    style={{
                                      contain: 'none',
                                      height: '25px',
                                    }}
                                  />
                                  <span>Create your first Feature</span>
                                </div>
                              </Button>
                            </FormGroup>
                          ))}
                        </div>
                      )
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
const FeaturesPageWithContext = (props) => {
  const context = useRouteContext()
  return <FeaturesPage {...props} routeContext={context} />
}

export default withRouter(ConfigProvider(FeaturesPageWithContext))
