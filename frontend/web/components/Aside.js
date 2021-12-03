import React, { Component } from 'react';
import propTypes from 'prop-types';
import NavLink from 'react-router-dom/NavLink';
import ProjectSelect from './ProjectSelect';
import AsideProjectButton from './AsideProjectButton';
import AsideTitleLink from './AsideTitleLink';
import Collapsible from './Collapsible';
import Popover from './base/Popover';
import ProjectSettingsIcon from './svg/ProjectSettingsIcon';
import AuditLogIcon from './svg/AuditLogIcon';
import OrgSettingsIcon from './svg/OrgSettingsIcon';
import EnvironmentDropdown from './EnvironmentDropdown';
import CreateProjectModal from './modals/CreateProject';
import LogoutIcon from './svg/LogoutIcon';
import UserSettingsIcon from './svg/UserSettingsIcon';
import DocumentationIcon from './svg/DocumentationIcon';
import NavIconSmall from './svg/NavIconSmall';
import PlusIcon from './svg/PlusIcon';
import FeaturesIcon from './svg/FeaturesIcon';
import UsersIcon from './svg/UsersIcon';
import SegmentsIcon from './svg/SegmentsIcon';
import EnvironmentSettingsIcon from './svg/EnvironmentSettingsIcon';
import ProjectStore from '../../common/stores/project-store';

const Aside = class extends Component {
  static displayName = 'Aside';

  static contextTypes = {
      router: propTypes.object.isRequired,
  };

  static propTypes = {
      className: propTypes.string,
      toggleAside: propTypes.func,
      asideIsVisible: propTypes.bool,
  };

  constructor(props, context) {
      super(props, context);
      this.state = {};
      AppActions.getProject(this.props.projectId);
  }

  componentWillReceiveProps(newProps) {
      if (newProps.projectId !== this.props.projectId) {
          AppActions.getProject(this.props.projectId);
      }
  }

  onProjectSave = () => {
      AppActions.refreshOrganisation();
  };

  toggleNav = () => {
      this.setState({ visible: !this.state.visible });
  };


  newProject = () => {
      openModal('Create  Project', <CreateProjectModal onSave={({ projectId, environmentId }) => {
          AppActions.getProject(projectId);
          this.context.router.history.push(`/project/${projectId}/environment/${environmentId}/features?new=true`);
      }}
      />);
  };

  render() {
      const { hasFeature, getValue, toggleAside, asideIsVisible } = this.props;
      let integrations = this.props.getValue('integrations') || '[]';
      integrations = JSON.parse(integrations);
      const hasRbacPermission = !this.props.hasFeature('plan_based_access') || Utils.getPlansPermission(AccountStore.getPlans(), 'AUDIT') || !this.props.hasFeature('scaleup_audit');
      return (
          <OrganisationProvider>
              {({ isLoading: isLoadingOrg, projects }) => (
                  <ProjectProvider id={this.props.projectId} onSave={this.onProjectSave}>
                      {({ isLoading, project }) => (
                          <React.Fragment>
                              <div
                                className={`aside ${this.props.className || ''}`} style={!asideIsVisible ? {
                                    width: 0,
                                    overflow: 'hidden',
                                } : isMobile ? { } : {}}
                              >
                                  {isMobile && (
                                  <div role="button" className="clickable toggle" onClick={toggleAside}>
                                      {!asideIsVisible ? <span className="icon ion-md-menu"/>
                                          : <span className="icon ion-md-close"/>}
                                  </div>
                                  )}
                                  <div className="row ml-0 mr-0 aside__wrapper">
                                      <div
                                        className={`aside__projects-sidebar ${this.props.className || ''}`}
                                      >
                                          <div className="flex-row justify-content-center">
                                              <div className="flex-column">
                                                  <Link to="/projects">
                                                      <NavIconSmall
                                                        className="aside__logo"
                                                      />
                                                  </Link>
                                              </div>

                                              <div className="flex-column">
                                                  <div className="aside__projects-item">
                                                      <div className="flex-row justify-content-center">
                                                          <div className="flex-column mb-3">

                                                              <Tooltip
                                                                title={(
                                                                    <Button onClick={this.newProject} className="btn--transparent aside__add-btn">
                                                                        <a
                                                                          id="create-project-link"
                                                                          to="/projects"
                                                                          state={{ create: true }}
                                                                        >
                                                                            <PlusIcon width={18}/>
                                                                        </a>
                                                                    </Button>
                                                                  )}
                                                                place="right"
                                                              >
                                                                  Create Project
                                                              </Tooltip>

                                                          </div>
                                                      </div>
                                                  </div>
                                              </div>

                                              <ProjectSelect
                                                renderRow={(project, onClick) => (
                                                    <AsideProjectButton
                                                      data-test={`switch-project-${project.name.toLowerCase()}${this.props.projectId === (`${project.id}`) ? '-active' : ''}`}
                                                      key={project.id}
                                                      onClick={onClick}
                                                      className={this.props.projectId === `${project.id}` ? 'active' : ''}
                                                      name={project.name}
                                                      projectLetter={(`${project.name[0]}`).toUpperCase()}
                                                    />
                                                )}
                                                projectId={this.props.projectId}
                                                environmentId={this.props.environmentId}
                                                clearableValue={false}
                                                onChange={(project) => {
                                                    AppActions.getProject(project.id);
                                                    if (project.environments[0]) {
                                                        this.context.router.history.push(`/project/${project.id}/environment/${project.environments[0].api_key}/features`);
                                                    } else {
                                                        this.context.router.history.push(`/project/${project.id}/environment/create`);
                                                    }
                                                    AsyncStorage.setItem('lastEnv', JSON.stringify({
                                                        orgId: AccountStore.getOrganisation().id,
                                                        projectId: project.id,
                                                        environmentId: project.environments[0].api_key,
                                                    }));
                                                }}
                                              />
                                          </div>
                                      </div>
                                      {(
                                          <React.Fragment>
                                              <div className="aside__main-content" style={{ 'overflowY': 'auto' }}>

                                                  <div className="pl-4 pr-4 pt-4">
                                                      <h1 className="aside__project-title">{project && project.name ? project.name : '...'}</h1>
                                                  </div>
                                                  <Permission level="project" permission="ADMIN" id={this.props.projectId}>
                                                      {({ permission, isLoading }) => permission && (
                                                      <NavLink
                                                        id="project-settings-link"
                                                        activeClassName="active"
                                                        className="aside__nav-item"
                                                        to={`/project/${this.props.projectId}/settings`}
                                                      >
                                                          <ProjectSettingsIcon className="aside__nav-item--icon"/>
                                                          Project Settings
                                                      </NavLink>
                                                      )}
                                                  </Permission>

                                                  <NavLink
                                                    to={`/project/${project.id}/environment/${(this.props.environmentId !== 'create' && this.props.environmentId) || (ProjectStore.model && ProjectStore.model.environments[0].api_key)}/segments`}

                                                    id="segments-link"
                                                    className="aside__nav-item"
                                                  >
                                                      <SegmentsIcon className="aside__nav-item--icon"/>
                                                      Segments
                                                  </NavLink>

                                                  <Permission level="project" permission="ADMIN" id={this.props.projectId}>
                                                      {({ permission, isLoading }) => permission && hasRbacPermission && (
                                                          <NavLink
                                                            id="audit-log-link"
                                                            activeClassName="active"
                                                            className="aside__nav-item"
                                                            to={`/project/${this.props.projectId}/environment/${this.props.environmentId}/audit-log`}
                                                          >
                                                              <AuditLogIcon className="aside__nav-item--icon"/>
                                                              Audit Log
                                                          </NavLink>
                                                      )}
                                                  </Permission>

                                                  {!hasRbacPermission && (
                                                      <Tooltip
                                                        title={(
                                                            <a href="#" className="aside__nav-item disabled">
                                                                <AuditLogIcon className="aside__nav-item--icon"/>
                                                                  Audit Log
                                                            </a>
                                                          )}
                                                      >
                                                          This feature is available with our scaleup plan
                                                      </Tooltip>
                                                  )}
                                                  {!!integrations.length && (
                                                      <Permission level="project" permission="CREATE_ENVIRONMENT" id={this.props.projectId}>
                                                          {({ permission, isLoading }) => permission && (
                                                              <NavLink
                                                                id="integrations-link"
                                                                activeClassName="active"
                                                                className="aside__nav-item"
                                                                to={`/project/${this.props.projectId}/integrations`}
                                                                exact
                                                              >
                                                                  <i className="icon mr-2 ion-ios-apps aside__nav-item--icon"/>
                                                                  Integrations
                                                              </NavLink>

                                                          )}
                                                      </Permission>
                                                  )}
                                                  <Permission level="project" permission="CREATE_ENVIRONMENT" id={this.props.projectId}>
                                                      {({ permission, isLoading }) => permission && (

                                                      <NavLink
                                                        id="create-env-link"
                                                        className="aside__header-link"
                                                        to={`/project/${this.props.projectId}/environment/create`}
                                                        exact
                                                      >
                                                          <AsideTitleLink
                                                            tooltip="Create Environment"
                                                            className="mt-4"
                                                            title="Environments"
                                                            iconClassName="ion-md-add"
                                                          />
                                                      </NavLink>

                                                      )}

                                                  </Permission>


                                                  {(
                                                      <div className="aside__environments-wrapper">
                                                          <EnvironmentDropdown
                                                            renderRow={(environment, onClick) => (
                                                                <Collapsible
                                                                  data-test={`switch-environment-${environment.name.toLowerCase()}${this.props.environmentId === (`${environment.api_key}`) ? '-active' : ''}`}
                                                                  onClick={onClick}
                                                                  active={environment.api_key === this.props.environmentId} title={environment.name}
                                                                >
                                                                    <Permission level="environment" permission="ADMIN" id={environment.api_key}>
                                                                        {({ permission: environmentAdmin, isLoading }) => (isLoading
                                                                            ? <div className="text-center"><Loader/></div> : (
                                                                                <div className="aside__environment-nav list-unstyled mb-0">
                                                                                    <NavLink
                                                                                      className="aside__environment-list-item"
                                                                                      id="features-link"
                                                                                      to={`/project/${project.id}/environment/${environment.api_key}/features`}
                                                                                    >
                                                                                        <FeaturesIcon className="aside__environment-list-item--icon"/>
                                                                                        Features
                                                                                    </NavLink>
                                                                                    {this.props.hasFeature('compare_environments') && (
                                                                                        <NavLink
                                                                                            id="integrations-link"
                                                                                            activeClassName="active"
                                                                                            className="aside__environment-list-item"
                                                                                            to={`/project/${this.props.projectId}/environment/${this.props.environmentId}/compare`}
                                                                                            exact
                                                                                        >
                                                                                            <span className="icon ion-ios-git-pull-request aside__environment-list-item--icon"/>
                                                                                            Compare
                                                                                        </NavLink>
                                                                                    )}
                                                                                    <NavLink
                                                                                      id="users-link"
                                                                                      className="aside__environment-list-item"
                                                                                      exact
                                                                                      to={`/project/${project.id}/environment/${environment.api_key}/users`}
                                                                                    >
                                                                                        <UsersIcon
                                                                                          className="aside__environment-list-item--icon"
                                                                                        />
                                                                                        Users
                                                                                    </NavLink>
                                                                                    {environmentAdmin && (
                                                                                    <NavLink
                                                                                      id="env-settings-link"
                                                                                      className="aside__environment-list-item"
                                                                                      to={`/project/${project.id}/environment/${environment.api_key}/settings`}
                                                                                    >
                                                                                        <EnvironmentSettingsIcon className="aside__environment-list-item--icon"/>
                                                                                            Settings
                                                                                    </NavLink>
                                                                                    )}
                                                                                </div>
                                                                            ))}
                                                                    </Permission>
                                                                </Collapsible>
                                                            )}
                                                            projectId={this.props.projectId}
                                                            environmentId={this.props.environmentId}
                                                            clearableValue={false}
                                                            onChange={(environment) => {
                                                                this.context.router.history.push(`/project/${this.props.projectId}/environment/${environment}/features`);
                                                                AsyncStorage.setItem('lastEnv', JSON.stringify({
                                                                    orgId: AccountStore.getOrganisation().id,
                                                                    projectId: this.props.projectId,
                                                                    environmentId: environment,
                                                                }));
                                                            }}
                                                          />
                                                      </div>

                                                  )}

                                                  <div className="flex flex-1"/>

                                                  <div className="aside__footer">
                                                      {hasFeature('demo_feature') && (
                                                      <a
                                                        style={{ color: getValue('demo_feature') || '#43424f' }}
                                                        className="aside__nav-item"
                                                        href="https://docs.flagsmith.com"
                                                      >
                                                          <i className="icon mr-2 ion-ios-star aside__nav-item--icon"/>
                                                          Super cool demo feature!
                                                      </a>
                                                      )}


                                                      {E2E && AccountStore.getOrganisationRole() === 'ADMIN' && (
                                                      <NavLink
                                                        id="organisation-settings-link"
                                                        activeClassName="active"
                                                        className="aside__nav-item"
                                                        to={`/project/${this.props.projectId}/environment/${this.props.environmentId}/organisation-settings`}
                                                      >
                                                          <OrgSettingsIcon className="aside__nav-item--icon"/>
                                                          Organisation
                                                      </NavLink>
                                                      )}

                                                      <a
                                                        href="https://docs.flagsmith.com"
                                                        target="_blank"
                                                        className="aside__nav-item hidden-sm-up"
                                                      >
                                                          <DocumentationIcon className="aside__nav-item--icon"/>
                                                          Documentation
                                                      </a>
                                                      <NavLink
                                                        id="account-settings-link"
                                                        className="aside__nav-item hidden-sm-up"
                                                        to={`/project/${this.props.projectId}/environment/${this.props.environmentId}/account`}
                                                      >
                                                          <UserSettingsIcon className="aside__nav-item--icon"/>
                                                          Account Settings
                                                      </NavLink>
                                                  </div>
                                              </div>
                                          </React.Fragment>
                                      )}
                                  </div>
                              </div>
                          </React.Fragment>
                      )}
                  </ProjectProvider>
              )}
          </OrganisationProvider>
      );
  }
};

module.exports = ConfigProvider(Aside);
