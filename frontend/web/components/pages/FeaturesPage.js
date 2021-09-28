import React, { Component } from 'react';
import EditIdentityModal from './UserPage';
import CreateFlagModal from '../modals/CreateFlag';
import ConfirmToggleFeature from '../modals/ConfirmToggleFeature';
import TryIt from '../TryIt';
import ConfirmRemoveFeature from '../modals/ConfirmRemoveFeature';
import TagSelect from '../TagSelect';
import HistoryIcon from '../HistoryIcon';
import TagValues from '../TagValues';
import withAuditWebhooks from '../../../common/providers/withAuditWebhooks';
import TagStore from '../../../common/stores/tags-store';
import { Tag } from '../AddEditTags';

const FeaturesPage = class extends Component {
    static displayName = 'FeaturesPage';

    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    constructor(props, context) {
        super(props, context);
        this.state = {
            tags: [],
            includeArchived: false,
        };
        ES6Component(this);
        this.listenTo(TagStore, 'loaded', () => {
            const tags = TagStore.model && TagStore.model[parseInt(this.props.match.params.projectId)];
            if (this.state.tags.length === 0 && tags && tags.length > 0) {
                this.setState({ tags: tags.map(v => v.id).concat('') });
            }
        });
        AppActions.getFeatures(this.props.match.params.projectId, this.props.match.params.environmentId);
    }

    componentWillUpdate(newProps) {
        const { match: { params } } = newProps;
        const { match: { params: oldParams } } = this.props;
        if (params.environmentId != oldParams.environmentId || params.projectId != oldParams.projectId) {
            this.getTags(params.projectId);
            AppActions.getFeatures(params.projectId, params.environmentId);
        }
    }

    componentDidMount = () => {
        API.trackPage(Constants.pages.FEATURES);
        const { match: { params } } = this.props;
        this.getTags(params.projectId);
        AsyncStorage.setItem('lastEnv', JSON.stringify({
            orgId: AccountStore.getOrganisation().id,
            projectId: params.projectId,
            environmentId: params.environmentId,
        }));
    };

    newFlag = () => {
        openModal('New Feature', <CreateFlagModal
          router={this.context.router}
          environmentId={this.props.match.params.environmentId}
          projectId={this.props.match.params.projectId}
        />, null, { className: 'side-modal fade' });
    };


    getTags = (projectId) => {
        AppActions.getTags(projectId);
        AsyncStorage.getItem(`${projectId}tags`).then((res) => {
            if (res) {
                this.setState({
                    tags: JSON.parse(res),
                });
            }
        });
    }

    editFlag = (projectFlag, environmentFlag) => {
        API.trackEvent(Constants.events.VIEW_FEATURE);
        openModal(`Edit Feature: ${projectFlag.name}`, <CreateFlagModal
          isEdit
          router={this.context.router}
          environmentId={this.props.match.params.environmentId}
          projectId={this.props.match.params.projectId}
          projectFlag={projectFlag}
          environmentFlag={environmentFlag}
          flagId={environmentFlag.id}
        />, null, { className: 'side-modal fade' });
    };


    componentWillReceiveProps(newProps) {
        if (newProps.match.params.environmentId != this.props.match.params.environmentId) {
            AppActions.getFeatures(newProps.match.params.projectId, newProps.match.params.environmentId);
        }
    }

    onSave = () => {
        toast('Environment Saved');
    };

    editIdentity = (id, envFlags) => {
        openModal(<EditIdentityModal id={id} envFlags={envFlags}/>);
    }

    confirmToggle = (projectFlag, environmentFlag, cb) => {
        openModal('Toggle Feature', <ConfirmToggleFeature
          environmentId={this.props.match.params.environmentId}
          projectFlag={projectFlag} environmentFlag={environmentFlag}
          cb={cb}
        />);
    }

    confirmRemove = (projectFlag, cb) => {
        openModal('Remove Feature', <ConfirmRemoveFeature
          environmentId={this.props.match.params.environmentId}
          projectFlag={projectFlag}
          cb={cb}
        />);
    }

    createFeaturePermission(el) {
        return (
            <Permission level="project" permission="CREATE_FEATURE" id={this.props.match.params.projectId}>
                {({ permission, isLoading }) => (permission ? (
                    el(permission)
                ) : this.renderWithPermission(permission, Constants.projectPermissions('Create Feature'), el(permission)))}
            </Permission>
        );
    }

    renderWithPermission(permission, name, el) {
        return permission ? (
            el
        ) : (
            <Tooltip
              title={<div>{el}</div>}
              place="right"
              html
            >{name}
            </Tooltip>
        );
    }

    onError = (error) => {
        // Kick user back out to projects
        this.setState({ error });
        if (typeof closeModal !== 'undefined') {
            closeModal();
            toast('We could not create this feature, please check the name is not in use.');
        }
    }

    filter = flags => _.filter(flags, (flag) => {
        if (!this.state.includeArchived && flag.is_archived) {
            return false;
        } if (!this.state.tags.length && this.state.includeArchived) {
            return true;
        }
        if (!this.state.length && !flag.is_archived) {
            return true;
        }
        if (this.state.tags.includes('') && (!flag.tags || !flag.tags.length)) {
            return true;
        }
        return _.intersection(flag.tags || [], this.state.tags).length;
    }) || []

    render() {
        const { projectId, environmentId } = this.props.match.params;
        const readOnly = this.props.hasFeature('read_only_mode');
        return (
            <div data-test="features-page" id="features-page" className="app-container container">
                <FeatureListProvider onSave={this.onSave} onError={this.onError}>
                    {({ isLoading, projectFlags, environmentFlags }, { environmentHasFlag, toggleFlag, editFlag, removeFlag }) => {
                        const archivedLength = projectFlags ? projectFlags.filter(v => v.is_archived === true).length : 0;
                        return (
                            <div className="features-page">
                                {isLoading && (!projectFlags || !projectFlags.length) && <div className="centered-container"><Loader/></div>}
                                {(!isLoading || (projectFlags && projectFlags.length)) && (
                                    <div>
                                        {projectFlags && projectFlags.length ? (
                                            <div>
                                                <Row>
                                                    <Flex>
                                                        <h3>Features</h3>
                                                        <p>
                                                            View and manage
                                                            {' '}
                                                            <Tooltip
                                                              title={<ButtonLink buttonText="feature flags" />}
                                                              place="right"
                                                            >
                                                                {Constants.strings.FEATURE_FLAG_DESCRIPTION}
                                                            </Tooltip>
                                                            {' '}
                                                            and
                                                            {' '}
                                                            {' '}
                                                            <Tooltip
                                                              title={<ButtonLink buttonText="remote config" />}
                                                              place="right"
                                                            >
                                                                {Constants.strings.REMOTE_CONFIG_DESCRIPTION}
                                                            </Tooltip>
                                                            {' '}
                                                            for
                                                            your selected environment.
                                                        </p>
                                                    </Flex>
                                                    <FormGroup className="float-right">
                                                        {projectFlags && projectFlags.length ? this.createFeaturePermission(perm => (
                                                            <div className="text-right">
                                                                <Button
                                                                  disabled={!perm || readOnly} data-test="show-create-feature-btn" id="show-create-feature-btn"
                                                                  onClick={this.newFlag}
                                                                >
                                                                        Create Feature
                                                                </Button>
                                                            </div>
                                                        ))
                                                            : null}
                                                    </FormGroup>
                                                </Row>
                                                <Permission level="environment" permission="ADMIN" id={this.props.match.params.environmentId}>
                                                    {({ permission, isLoading }) => (
                                                        <FormGroup className="mb-4">
                                                            <PanelSearch
                                                              className="no-pad"
                                                              id="features-list"
                                                              icon="ion-ios-rocket"
                                                              title="Features"
                                                              renderSearchWithNoResults
                                                              sorting={[
                                                                  { label: 'Name', value: 'name', order: 'asc', default: true },
                                                                  { label: 'Created Date', value: 'created_date', order: 'asc' },
                                                              ]}
                                                              items={this.filter(projectFlags, this.state.tags)}
                                                              header={(
                                                                  <Row style={{ backgroundColor: '#f7f7f7' }}>
                                                                      <TagSelect
                                                                        showUntagged
                                                                        showClearAll
                                                                        projectId={projectId} value={this.state.tags} onChange={(tags) => {
                                                                            this.setState({ tags });
                                                                            AsyncStorage.setItem(`${projectId}tags`, JSON.stringify(tags));
                                                                        }}
                                                                      >
                                                                          {!!archivedLength && (
                                                                              <div className="mr-2 mb-2">
                                                                                  <Tag
                                                                                    selected={this.state.includeArchived}
                                                                                    onClick={() => this.setState({ includeArchived: !this.state.includeArchived })}
                                                                                    className="px-2 py-2 ml-2 mr-2"
                                                                                    tag={{ label: `Archived (${archivedLength})` }}
                                                                                  />
                                                                              </div>

                                                                          )}
                                                                      </TagSelect>
                                                                  </Row>
                                                                )}
                                                              renderRow={(projectFlag, i) => {
                                                                  const { name, id, enabled, created_date, description, type } = projectFlag;
                                                                  return (
                                                                      <Row
                                                                        style={{ flexWrap: 'nowrap' }}
                                                                        className={permission ? 'list-item clickable' : 'list-item'} key={id} space
                                                                        data-test={`feature-item-${i}`}
                                                                      >
                                                                          <div
                                                                            style={{ overflow: 'hidden' }}
                                                                            className="flex flex-1"
                                                                            onClick={() => !readOnly && permission && this.editFlag(projectFlag, environmentFlags[id])}
                                                                          >
                                                                              <div>
                                                                                  <ButtonLink>
                                                                                      {name}
                                                                                  </ButtonLink>
                                                                              </div>
                                                                              <div className="list-item-footer faint">
                                                                                  <Row>
                                                                                      {(
                                                                                          <TagValues projectId={projectId} value={projectFlag.tags}/>
                                                                                        )}
                                                                                      <div>
                                                                                            Created {moment(created_date).format('Do MMM YYYY HH:mma')}{' - '}
                                                                                          {description || 'No description'}
                                                                                      </div>
                                                                                  </Row>
                                                                              </div>
                                                                          </div>
                                                                          <Row>
                                                                              {
                                                                                    this.renderWithPermission(permission, Constants.environmentPermissions('Admin'), (
                                                                                        <Row style={{
                                                                                            marginTop: 5,
                                                                                            marginBottom: 5,
                                                                                            marginRight: 15,
                                                                                        }}
                                                                                        >
                                                                                            <Column>
                                                                                                <FeatureValue
                                                                                                  onClick={() => permission && !readOnly && this.editFlag(projectFlag, environmentFlags[id])}
                                                                                                  value={environmentFlags[id] && environmentFlags[id].feature_state_value}
                                                                                                  data-test={`feature-value-${i}`}
                                                                                                />
                                                                                            </Column>
                                                                                            <Column>
                                                                                                <Switch
                                                                                                  disabled={!permission || readOnly}
                                                                                                  data-test={`feature-switch-${i}${environmentFlags[id] && environmentFlags[id].enabled ? '-on' : '-off'}`}
                                                                                                  checked={environmentFlags[id] && environmentFlags[id].enabled}
                                                                                                  onChange={() => this.confirmToggle(projectFlag, environmentFlags[id], (environments) => {
                                                                                                      toggleFlag(_.findIndex(projectFlags, { id }), environments);
                                                                                                  })}
                                                                                                />
                                                                                            </Column>
                                                                                        </Row>
                                                                                    ))
                                                                                }

                                                                              {AccountStore.getOrganisationRole() === 'ADMIN' && (
                                                                              <Tooltip
                                                                                html
                                                                                title={(
                                                                                    <button
                                                                                      onClick={() => {
                                                                                          this.context.router.history.push(`/project/${projectId}/environment/${environmentId}/audit-log?env=${environmentId}&search=${projectFlag.name}`);
                                                                                      }}
                                                                                      className="btn btn--with-icon"
                                                                                      data-test={`feature-history-${i}`}
                                                                                    >
                                                                                        <HistoryIcon/>
                                                                                    </button>
                                                                                        )}
                                                                              >
                                                                                        Feature history
                                                                              </Tooltip>
                                                                              )}
                                                                              <Permission level="project" permission="DELETE_FEATURE" id={this.props.match.params.projectId}>
                                                                                  {({ permission: removeFeaturePermission }) => this.renderWithPermission(removeFeaturePermission, Constants.projectPermissions('Delete Feature'), (
                                                                                      <Column>
                                                                                          <Tooltip
                                                                                            html
                                                                                            title={(
                                                                                                <button
                                                                                                  disabled={!removeFeaturePermission || readOnly}
                                                                                                  onClick={() => this.confirmRemove(projectFlag, () => {
                                                                                                      removeFlag(this.props.match.params.projectId, projectFlag);
                                                                                                  })}
                                                                                                  className="btn btn--with-icon"
                                                                                                  data-test={`remove-feature-btn-${i}`}
                                                                                                >
                                                                                                    <RemoveIcon/>
                                                                                                </button>
                                                                                                )}
                                                                                          >
                                                                                                Remove feature
                                                                                          </Tooltip>
                                                                                      </Column>
                                                                                  ))}
                                                                              </Permission>
                                                                          </Row>
                                                                      </Row>
                                                                  );
                                                              }}
                                                              filterRow={({ name }, search) => name.toLowerCase().indexOf(search) > -1}
                                                            />
                                                        </FormGroup>
                                                    )}

                                                </Permission>
                                                <FormGroup>
                                                    <CodeHelp
                                                      title="1: Installing the SDK"
                                                      snippets={Constants.codeHelp.INSTALL}
                                                    />
                                                    <CodeHelp
                                                      title="2: Initialising your project"
                                                      snippets={Constants.codeHelp.INIT(this.props.match.params.environmentId, projectFlags && projectFlags[0] && projectFlags[0].name)}
                                                    />
                                                </FormGroup>
                                                <FormGroup>
                                                    <TryIt
                                                      title="Test what values are being returned from the API on this environment"
                                                      environmentId={this.props.match.params.environmentId}
                                                    />
                                                </FormGroup>
                                            </div>
                                        ) : (
                                            <div>
                                                <h3>Brilliant! Now create your features.</h3>

                                                <FormGroup>
                                                    <Panel icon="ion-ios-rocket" title="1. creating a feature">
                                                        <p>
                                                            You can create two types of features for your project:
                                                            <ul>
                                                                <li>
                                                                    <strong>Feature Flags</strong>
                                                                    : These allows you to
                                                                    toggle
                                                                    features on and off:
                                                                    <p className="faint">
                                                                        EXAMPLE: You're working on a new messaging feature
                                                                        for
                                                                        your app but only show it on develop.
                                                                    </p>
                                                                </li>
                                                                <li>
                                                                    <strong>Remote configuration</strong>
                                                                    : configuration for
                                                                    a
                                                                    particular feature
                                                                    <p className="faint">
                                                                        EXAMPLE: This could be absolutely anything from a
                                                                        font size for a website/mobile app or an environment
                                                                        variable
                                                                        for a server
                                                                    </p>
                                                                </li>
                                                            </ul>
                                                        </p>
                                                    </Panel>
                                                </FormGroup>
                                                <FormGroup>
                                                    <Panel
                                                      icon="ion-ios-settings"
                                                      title="2. configuring features per environment"
                                                    >
                                                        <p>
                                                            We've created 2 environments for
                                                            you
                                                            {' '}
                                                            <strong>Development</strong>
                                                            {' '}
                                                            and
                                                            {' '}
                                                            <strong>Production</strong>
                                                            .
                                                            When
                                                            you create a feature it makes copies of them for each
                                                            environment,
                                                            allowing you to edit the values separately. You can create more
                                                            environments too if you need to.
                                                        </p>
                                                    </Panel>
                                                </FormGroup>

                                                <FormGroup>
                                                    <Panel
                                                      icon="ion-ios-person"
                                                      title="3. configuring features per user"
                                                    >
                                                        <p>
                                                            When users login to your application, you
                                                            can
                                                            {' '}
                                                            <strong>identify</strong>
                                                            {' '}
                                                            them using one of our SDKs, this
                                                            will add
                                                            them to the users page.
                                                            From there you can configure their features. We've created an
                                                            example user for you which you can see in the
                                                            {' '}
                                                            <Link
                                                              className="btn--link"
                                                              to={`/project/${projectId}/environment/${environmentId}/users`}
                                                            >
                                                                Users
                                                                page
                                                            </Link>.
                                                            <p className="faint">
                                                                EXAMPLE: You're working on a new messaging feature for your
                                                                app but
                                                                only show it for that user.
                                                            </p>
                                                        </p>
                                                    </Panel>
                                                </FormGroup>
                                                {this.createFeaturePermission(perm => (
                                                    <FormGroup className="text-center">
                                                        <Button
                                                          disabled={!perm}
                                                          className="btn-lg btn-primary" id="show-create-feature-btn" data-test="show-create-feature-btn"
                                                          onClick={this.newFlag}
                                                        >
                                                            <span className="icon ion-ios-rocket"/>
                                                            {' '}
                                                            Create your first Feature
                                                        </Button>
                                                    </FormGroup>
                                                ))}
                                            </div>
                                        )}

                                    </div>
                                )}
                            </div>
                        );
                    }}
                </FeatureListProvider>
            </div>
        );
    }
};

FeaturesPage.propTypes = {};

module.exports = hot(module)(ConfigProvider(FeaturesPage));
