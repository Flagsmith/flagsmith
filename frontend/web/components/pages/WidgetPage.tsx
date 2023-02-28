import React, { Component, useEffect, useState } from 'react';
import TagFilter from '../tags/TagFilter';
import Tag from '../tags/Tag';
import FeatureRow from '../FeatureRow';
import FeatureListStore from 'common/stores/feature-list-store';
import ProjectStore from 'common/stores/project-store';
import API from '../../project/api';
import { getStore } from 'common/store';
import Permission from 'common/providers/Permission';
import Constants from 'common/constants';
import Utils from 'common/utils/utils';
import { Provider } from 'react-redux';
import InfoMessage from '../InfoMessage';
import PanelSearch from '../PanelSearch';
// @ts-ignore
import { AsyncStorage } from 'polyfill-react-native';
import { FeatureListProviderActions, FeatureListProviderData } from '../../../global';
import { Environment, PagedResponse, ProjectFlag } from 'common/types/responses';
import { useCustomWidgetOptionString } from '@datadog/ui-extensions-react';
import client from '../datadog-client';
import { resolveAuthFlow } from '@datadog/ui-extensions-sdk';
import AuditLog from '../AuditLog';
import OrgEnvironmentSelect from '../OrgEnvironmentSelect';

const FeatureListProvider = require('common/providers/FeatureListProvider')
const AppActions = require("common/dispatcher/app-actions")
const ES6Component = require("common/ES6Component")
let isWidget = false;
export const getIsWidget = ()=> {
    return isWidget;
}

type FeatureListType = {
    projectId: string
    environmentId: string
    pageSize: number
    hideTags: boolean
}


const PermissionError = ()=> {
    return (
        <InfoMessage>
            Please check you have access to the project and environment within the widget settings.
        </InfoMessage>
    )
}

const FeatureList = class extends Component<FeatureListType> {
    state =  {
        tags: [] as string[],
        error:null,
        showArchived: false,
        search: null,
        sort: { label: 'Name', sortBy: 'name', sortOrder: 'asc' },
    }
    constructor(props:any, context:any) {
        super(props, context);
        ES6Component(this);
        AppActions.getProject(this.props.projectId);
        AppActions.getFeatures(this.props.projectId, this.props.environmentId, true, this.state.search, this.state.sort, 0, this.getFilter(), this.props.pageSize);
    }

    componentDidUpdate(prevProps: Readonly<FeatureListType>, prevState: Readonly<{}>, snapshot?: any) {
        if( (this.props.projectId !== prevProps.projectId)) {
            AppActions.getProject(this.props.projectId);

        }
        if( (this.props.projectId !== prevProps.projectId) ||
            (this.props.environmentId !== prevProps.environmentId) ||
            (this.props.pageSize !== prevProps.pageSize)
        ) {
            AppActions.getFeatures(this.props.projectId, this.props.environmentId, true, this.state.search, this.state.sort, 0, this.getFilter(), this.props.pageSize);
        }
    }

    componentDidMount = () => {
        API.trackPage(Constants.pages.FEATURES);
    };

    getFilter = () => ({
        tags: !this.state.tags || !this.state.tags.length ? undefined : this.state.tags.join(','),
        is_archived: this.state.showArchived,
    })

    onSave = () => {
        toast('Saved');
    };

    onError = (error) => {
        // Kick user back out to projects
        this.setState({ error: true });
        toast('We could not create this feature, please check the name is not in use.');
    }

    filter = () => {
        AppActions.searchFeatures(this.props.projectId, this.props.environmentId, true, this.state.search, this.state.sort, 0, this.getFilter(), this.props.pageSize);
    }

    render() {
        const { projectId, environmentId } = this.props;
        const environment = ProjectStore.getEnvironment(environmentId) as Environment|null;
        return (
            <Provider store={getStore()}>
                <div className="widget-container" data-test="features-page" id="features-page">
                    <FeatureListProvider onSave={this.onSave}>
                    {({ projectFlags, environmentFlags, isLoading, error }: FeatureListProviderData, { toggleFlag, removeFlag }: FeatureListProviderActions) => {
                        if(error) {
                            return <PermissionError/>
                        }
                        return (
                                <div>
                                    {projectFlags?.length===0 && <div>
                                        This project has no feature flags to display
                                    </div>}
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
                                                                    onChange={(e:InputEvent) => {
                                                                        this.setState({ search: Utils.safeParseEventValue(e) }, () => {
                                                                            AppActions.searchFeatures(this.props.projectId, this.props.environmentId, true, this.state.search, this.state.sort, 0, this.getFilter(),this.props.pageSize);
                                                                        });
                                                                    }}
                                                                    nextPage={() => AppActions.getFeatures(this.props.projectId, this.props.environmentId, true, this.state.search, this.state.sort, (FeatureListStore.paging as PagedResponse<ProjectFlag>).next||1, this.getFilter(), this.props.pageSize)}
                                                                    prevPage={() => AppActions.getFeatures(this.props.projectId, this.props.environmentId, true, this.state.search, this.state.sort, (FeatureListStore.paging as PagedResponse<ProjectFlag>).previous, this.getFilter(), this.props.pageSize)}
                                                                    goToPage={(page:number) => AppActions.getFeatures(this.props.projectId, this.props.environmentId, true, this.state.search, this.state.sort, page, this.getFilter())}
                                                                    onSortChange={(sort:string) => {
                                                                        this.setState({ sort }, () => {
                                                                            AppActions.getFeatures(this.props.projectId, this.props.environmentId, true, this.state.search, this.state.sort, 0, this.getFilter(), this.props.pageSize);
                                                                        });
                                                                    }}
                                                                    sorting={[
                                                                        { label: 'Name', value: 'name', order: 'asc', default: true },
                                                                        { label: 'Created Date', value: 'created_date', order: 'asc' },
                                                                    ]}
                                                                    items={projectFlags}
                                                                    header={this.props.hideTags? null : (
                                                                      <Row className="px-0 pt-0">
                                                                          <TagFilter
                                                                              showUntagged
                                                                              showClearAll={(this.state.tags && !!this.state.tags.length) || this.state.showArchived}
                                                                              onClearAll={() => this.setState({ showArchived: false, tags: [] }, this.filter)}
                                                                              projectId={`${projectId}`} value={this.state.tags} onChange={(tags) => {
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
                                                                              <div className="mr-2">
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
                                                                          </TagFilter>
                                                                      </Row>
                                                                    )}
                                                                    renderRow={(projectFlag:ProjectFlag, i:number) => (
                                                                        <FeatureRow
                                                                            hideRemove
                                                                            hideAudit
                                                                            widget
                                                                            readOnly
                                                                            environmentFlags={environmentFlags}
                                                                            projectFlags={projectFlags}
                                                                            permission={permission}
                                                                            environmentId={environmentId}
                                                                            projectId={projectId}
                                                                            index={i}
                                                                            toggleFlag={toggleFlag}
                                                                            removeFlag={removeFlag}
                                                                            projectFlag={projectFlag}
                                                                        />
                                                                    )}
                                                                    filterRow={() => true}
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
            </Provider>
        )
    }
}



export default function Widget() {
    useEffect(()=>{
        document.body.classList.add("widget-mode")
    },[])
    const projectId = useCustomWidgetOptionString(client, 'Project');
    const environmentId = useCustomWidgetOptionString(client, 'Environment');
    const pageSize = useCustomWidgetOptionString(client, 'PageSize') || "5";
  // @ts-ignore context is marked as private but is accessible and needed
    const id = client.context?.widget?.definition?.custom_widget_key;
    const isAudit = id === "flagsmith_audit_widget";
    const hideTags = useCustomWidgetOptionString(client, 'HideTags') === "Yes";
    const [error, setError] = useState<boolean>(false);
    const [_projectId, setProjectId] = useState<string|null>(projectId||null);
    const [_environmentId, setEnvironmentId] = useState<string|null>(environmentId||null);
    const [organisationId, setOrganisationId] = useState<string|null>(null);
    isWidget = true;

    useEffect(()=>{
        setProjectId(environmentId||null)
    },[environmentId])

    useEffect(()=>{
        setProjectId(projectId||null)
    },[projectId])

    if (!API.getCookie("t")) {
        resolveAuthFlow({
            isAuthenticated: false,
        });
        return null
    }

    if(error) {
        return <PermissionError/>
    }
    if (projectId && environmentId && !error) {
        if (isAudit) {
            return (
                <Provider store={getStore()}>
                    <div className="widget-container">
                        <AuditLog onErrorChange={setError} environmentId={environmentId} projectId={projectId} pageSize={parseInt(pageSize)}/>
                    </div>
                </Provider>
            )
        }
        return <FeatureList hideTags={hideTags} pageSize={parseInt(pageSize)} projectId={`${projectId}`} environmentId={`${environmentId}`}/>
    }

    return <div className="text-center pt-5">
        <h3>Please select the environment you wish to use.</h3>
        <div className="widget-container">
            <Provider store={getStore()}>
                <OrgEnvironmentSelect
                    useApiKey={!isAudit}
                    organisationId={organisationId}
                    environmentId={_environmentId}
                    projectId={_projectId}
                    onOrganisationChange={setOrganisationId}
                    onProjectChange={setProjectId}
                    onEnvironmentChange={setEnvironmentId}
                />
            </Provider>
        </div>
    </div>
}
