import React, { Component } from 'react';
import TryIt from '../TryIt';
import TagSelect from '../TagSelect';
import TagStore from '../../../common/stores/tags-store';
import { Tag } from '../AddEditTags';
import FeatureRow from '../FeatureRow';
import FeatureListStore from '../../../common/stores/feature-list-store';
import ProjectStore from '../../../common/stores/project-store';
import { useCustomWidgetOptionString } from '@datadog/ui-extensions-react';
import { init } from '@datadog/ui-extensions-sdk';

const client = init();
const pageSize = 8;
const WidgetPage = class extends Component {
    static displayName = 'WidgetPage';

    static propTypes = {
        projectId: RequiredString,
        environmentIdId: RequiredString,
    };

    constructor(props, context) {
        super(props, context);
        this.state = {
            tags: [],
            showArchived: false,
            search: null,
            sort: { label: 'Name', sortBy: 'name', sortOrder: 'asc' },
        };
        ES6Component(this);
        this.listenTo(TagStore, 'loaded', () => {
            const tags = TagStore.model && TagStore.model[parseInt(this.props.projectId)];
        });
        AppActions.getProject(this.props.projectId);
        AppActions.getFeatures(this.props.projectId, this.props.environmentId, true, this.state.search, this.state.sort, 0, this.getFilter(), pageSize);
    }

    componentWillUnmount() {
        document.body.classList.remove("widget-mode")
    }
    componentWillUnmount() {
        document.body.classList.add("widget-mode")
    }

    componentDidMount = () => {
        API.trackPage(Constants.pages.FEATURES);
        this.getTags(this.props.projectId);
    };

    getTags = (projectId) => {
        AppActions.getTags(projectId);
    }

    getFilter = () => ({
        tags: !this.state.tags || !this.state.tags.length ? undefined : this.state.tags.join(','),
        is_archived: this.state.showArchived,
    })

    onSave = () => {
        toast('Saved');
    };

    onError = (error) => {
        // Kick user back out to projects
        this.setState({ error });
        if (typeof closeModal !== 'undefined') {
            closeModal();
            toast('We could not create this feature, please check the name is not in use.');
        }
    }

    filter = () => {
        AppActions.searchFeatures(this.props.projectId, this.props.environmentId, true, this.state.search, this.state.sort, 0, this.getFilter(), pageSize);
    }

    createFeaturePermission(el) {
        return (
            <Permission level="project" permission="CREATE_FEATURE" id={this.props.projectId}>
                {({ permission, isLoading }) => (permission ? (
                    el(permission)
                ) : Utils.renderWithPermission(permission, Constants.projectPermissions('Create Feature'), el(permission)))}
            </Permission>
        );
    }

    render() {
        const { projectId, environmentId } = this.props;
        const readOnly = Utils.getFlagsmithHasFeature('read_only_mode');
        const environment = ProjectStore.getEnvironment(environmentId);

        return (
            <div data-test="features-page" id="features-page" style={{padding:10}}>
                <FeatureListProvider onSave={this.onSave} onError={this.onError}>
                    {({ projectFlags, environmentFlags }, { environmentHasFlag, toggleFlag, editFlag, removeFlag }) => {
                        const isLoading = FeatureListStore.isLoading;
                        return (
                            <div>
                                {isLoading && (!projectFlags || !projectFlags.length) && <div className="centered-container"><Loader/></div>}
                                {(!isLoading || (projectFlags && !!projectFlags.length)) && (
                                    <div>
                                        {(projectFlags && projectFlags.length) || ((this.state.showArchived || typeof this.state.search === 'string' || !!this.state.tags.length) && !isLoading) ? (
                                            <div>
                                                <Permission level="environment" permission={Utils.getManageFeaturePermission(Utils.changeRequestsEnabled(environment && environment.minimum_change_request_approvals))} id={this.props.environmentId}>
                                                    {({ permission, isLoading }) => (
                                                        <div>
                                                            <PanelSearch
                                                              className="no-pad"
                                                              id="features-list"
                                                              icon="ion-ios-rocket"
                                                              title="Features"
                                                              renderSearchWithNoResults
                                                              itemHeight={65}
                                                              isLoading={FeatureListStore.isLoading}
                                                              paging={FeatureListStore.paging}
                                                              search={this.state.search}
                                                              onChange={(e) => {
                                                                  this.setState({ search: Utils.safeParseEventValue(e) }, () => {
                                                                      AppActions.searchFeatures(this.props.projectId, this.props.environmentId, true, this.state.search, this.state.sort, 0, this.getFilter(),pageSize);
                                                                  });
                                                              }}
                                                              nextPage={() => AppActions.getFeatures(this.props.projectId, this.props.environmentId, true, this.state.search, this.state.sort, FeatureListStore.paging.next, this.getFilter(), pageSize)}
                                                              prevPage={() => AppActions.getFeatures(this.props.projectId, this.props.environmentId, true, this.state.search, this.state.sort, FeatureListStore.paging.previous, this.getFilter(), pageSize)}
                                                              goToPage={page => AppActions.getFeatures(this.props.projectId, this.props.environmentId, true, this.state.search, this.state.sort, page, this.getFilter())}
                                                              onSortChange={(sort) => {
                                                                  this.setState({ sort }, () => {
                                                                      AppActions.getFeatures(this.props.projectId, this.props.environmentId, true, this.state.search, this.state.sort, 0, this.getFilter(), pageSize);
                                                                  });
                                                              }}
                                                              sorting={[
                                                                  { label: 'Name', value: 'name', order: 'asc', default: true },
                                                                  { label: 'Created Date', value: 'created_date', order: 'asc' },
                                                              ]}
                                                              items={projectFlags}
                                                              header={(
                                                                  <Row className="px-0 pt-0 pb-2">
                                                                      <TagSelect
                                                                        showUntagged
                                                                        showClearAll={(this.state.tags && !!this.state.tags.length) || this.state.showArchived}
                                                                        onClearAll={() => this.setState({ showArchived: false, tags: [] }, this.filter)}
                                                                        projectId={projectId} value={this.state.tags} onChange={(tags) => {
                                                                            FeatureListStore.isLoading = true;
                                                                            if (tags.includes('') && tags.length>1) {
                                                                                if (!this.state.tags.includes('')) {
                                                                                    this.setState({ tags: [''] }, this.filter);
                                                                                } else {
                                                                                    this.setState({ tags: tags.filter(v => !!v) }, this.filter);
                                                                                }
                                                                            } else {
                                                                                this.setState({ tags }, this.filter);
                                                                            }
                                                                            AsyncStorage.setItem(`${projectId}tags`, JSON.stringify(tags));
                                                                        }}
                                                                      >
                                                                          <div className="mr-2 mb-2">
                                                                              <Tag
                                                                                selected={this.state.showArchived}
                                                                                onClick={() => {
                                                                                    FeatureListStore.isLoading = true;
                                                                                    this.setState({ showArchived: !this.state.showArchived }, this.filter);
                                                                                }}
                                                                                className="px-2 py-2 ml-2 mr-2"
                                                                                tag={{ label: 'Archived' }}
                                                                              />
                                                                          </div>
                                                                      </TagSelect>
                                                                  </Row>
                                                                )}
                                                              renderRow={(projectFlag, i) => (
                                                                  <FeatureRow
                                                                    hideRemove
                                                                    hideAudit
                                                                    environmentFlags={environmentFlags}
                                                                    projectFlags={projectFlags}
                                                                    permission={permission}
                                                                    environmentId={environmentId}
                                                                    projectId={projectId}
                                                                    index={i} canDelete={permission}
                                                                    toggleFlag={toggleFlag}
                                                                    editFlag={editFlag}
                                                                    removeFlag={removeFlag}
                                                                    projectFlag={projectFlag}
                                                                  />
                                                              )}
                                                              filterRow={({ name }, search) => true}
                                                            />
                                                        </div>
                                                    )}

                                                </Permission>
                                            </div>
                                        ) : null}
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

const WidgetPageWrapper = ({}) => {
    // const projectId = useCustomWidgetOptionString(client, 'project');
    // const environmentId = useCustomWidgetOptionString(client, 'environment');

    const projectId = "12"
    const environmentId = "Ueo6zkrS8kt4LzuaJF9NFJ"
    return (
        <WidgetPage projectId={projectId} environmentId={environmentId}/>
    );
};

export default WidgetPageWrapper;
