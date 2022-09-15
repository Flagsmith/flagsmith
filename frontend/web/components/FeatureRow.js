import React, { FunctionComponent, Component } from 'react';
import TagValues from './TagValues';
import HistoryIcon from './HistoryIcon';
import ConfirmToggleFeature from './modals/ConfirmToggleFeature';
import ConfirmRemoveFeature from './modals/ConfirmRemoveFeature';
import CreateFlagModal from './modals/CreateFlag';
import TagStore from '../../common/stores/tags-store'; // we need this to make JSX compile
import ProjectStore from '../../common/stores/project-store'; // we need this to make JSX compile


class TheComponent extends Component {
    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    state = {};

    confirmToggle = (projectFlag, environmentFlag, cb) => {
        openModal('Toggle Feature', <ConfirmToggleFeature
          environmentId={this.props.environmentId}
          projectFlag={projectFlag} environmentFlag={environmentFlag}
          cb={cb}
        />);
    }

    componentDidMount() {
        const { projectFlag, environmentFlags } = this.props;
        const {feature, tab} = Utils.fromParam()
        const {  id } = projectFlag;
        if (`${id}` === feature) {
            this.editFlag(projectFlag, environmentFlags[id],tab);
        }
    }

    confirmRemove = (projectFlag, cb) => {
        openModal('Remove Feature', <ConfirmRemoveFeature
          environmentId={this.props.environmentId}
          projectFlag={projectFlag}
          cb={cb}
        />);
    }

    editFlag = (projectFlag, environmentFlag,tab) => {
        API.trackEvent(Constants.events.VIEW_FEATURE);

        history.replaceState(
            {},
            null,
            `${document.location.pathname}?feature=${projectFlag.id}${tab?`&tab=${tab}`:""}`
        );
        openModal(`Edit Feature: ${projectFlag.name}`, <CreateFlagModal
          isEdit
          router={this.context.router}
          environmentId={this.props.environmentId}
          projectId={this.props.projectId}
          projectFlag={projectFlag}
          environmentFlag={environmentFlag}
          flagId={environmentFlag.id}
        />, null, { className: 'side-modal fade', onClose: ()=>{
                history.replaceState(
                    {},
                    null,
                    `${document.location.pathname}`
                );
            } });
    };


    render() {
        const { projectId, projectFlag, permission, environmentFlags, environmentId, projectFlags, removeFlag, toggleFlag } = this.props;
        const { name, id, enabled, created_date, description, type } = this.props.projectFlag;
        const readOnly = Utils.getFlagsmithHasFeature('read_only_mode');
        const isProtected = TagStore.hasProtectedTag(projectFlag, parseInt(projectId));
        const environment = ProjectStore.getEnvironment(environmentId);
        if (this.props.condensed) {
            return Utils.renderWithPermission(permission, Constants.environmentPermissions(Utils.getManageFeaturePermissionDescription()), (
                <Row
                    onClick={() => permission && !readOnly && this.editFlag(projectFlag, environmentFlags[id])}
                    style={{ overflow: 'hidden', ...(this.props.style || {}) }}>
                    <div className={`mr-2 ${this.props.fadeEnabled && 'faded'}`}>
                        <Switch
                          disabled={!permission || readOnly}
                          data-test={`feature-switch-${this.props.index}${environmentFlags[id] && environmentFlags[id].enabled ? '-on' : '-off'}`}
                          checked={environmentFlags[id] && environmentFlags[id].enabled}
                          onChange={() => {
                              if (Utils.changeRequestsEnabled(environment.minimum_change_request_approvals)) {
                                  this.editFlag(projectFlag, environmentFlags[id]);
                                  return;
                              }
                              this.confirmToggle(projectFlag, environmentFlags[id], (environments) => {
                                  toggleFlag(_.findIndex(projectFlags, { id }), environments, null, this.props.environmentFlags, this.props.projectFlags);
                              });
                          }}
                        />
                    </div>
                    <div className={`mr-2 clickable ${this.props.fadeValue && 'faded'}`}>
                        <FeatureValue
                          onClick={() => permission && !readOnly && this.editFlag(projectFlag, environmentFlags[id])}
                          value={environmentFlags[id] && environmentFlags[id].feature_state_value}
                          data-test={`feature-value-${this.props.index}`}
                        />
                    </div>
                </Row>
            ));
        }

        return (
            <Row
              style={{ flexWrap: 'nowrap' }}
              className={this.props.canDelete ? 'list-item clickable py-2' : 'list-item py-1'} key={id} space
              data-test={`feature-item-${this.props.index}`}
            >
                <div
                  className="flex flex-1"
                  onClick={() => !readOnly && permission && this.editFlag(projectFlag, environmentFlags[id])}
                >
                    <div>
                        <ButtonLink>
                            {name}
                        </ButtonLink>
                        {projectFlag.owners && !!projectFlag.owners.length ? (
                            <Tooltip
                              title={(
                                  <ButtonLink>
                                      <ion className="ion ion-md-person px-2"/>
                                  </ButtonLink>
)}
                              place="right"
                            >
                                {`Flag assigned to ${projectFlag.owners.map(v => `${v.first_name} ${v.last_name}`).join(', ')}`}
                            </Tooltip>

                        ) : (
                            <span/>
                        )}
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
                    Utils.renderWithPermission(permission, Constants.environmentPermissions(Utils.getManageFeaturePermissionDescription()), (
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
                                  data-test={`feature-value-${this.props.index}`}
                                />
                            </Column>
                            <Column>
                                <Switch
                                  disabled={!permission || readOnly}
                                  data-test={`feature-switch-${this.props.index}${environmentFlags[id] && environmentFlags[id].enabled ? '-on' : '-off'}`}
                                  checked={environmentFlags[id] && environmentFlags[id].enabled}
                                  onChange={() => {
                                      if (Utils.changeRequestsEnabled(environment.minimum_change_request_approvals)) {
                                          this.editFlag(projectFlag, environmentFlags[id]);
                                          return;
                                      }
                                      this.confirmToggle(projectFlag, environmentFlags[id], (environments) => {
                                          toggleFlag(_.findIndex(projectFlags, { id }), environments);
                                      });
                                  }}
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
                            data-test={`feature-history-${this.props.index}`}
                          >
                              <HistoryIcon/>
                          </button>
                        )}
                    >
                        Feature history
                    </Tooltip>
                    )}
                    <Permission level="project" permission="DELETE_FEATURE" id={projectId}>
                        {({ permission: removeFeaturePermission }) => Utils.renderWithPermission(removeFeaturePermission, Constants.projectPermissions('Delete Feature'), (
                            <Column>
                                <Tooltip
                                  html
                                  title={(
                                      <button
                                        disabled={!removeFeaturePermission || readOnly || isProtected}
                                        onClick={() => this.confirmRemove(projectFlag, () => {
                                            removeFlag(projectId, projectFlag);
                                        })}
                                        className="btn btn--with-icon"
                                        data-test={`remove-feature-btn-${this.props.index}`}
                                      >
                                          <RemoveIcon/>
                                      </button>
                                )}
                                >
                                    {isProtected ? '<span>This feature has tagged as <bold>protected</bold>, <bold>permanent</bold>, <bold>do not delete</bold>, or <bold>read only</bold>. Please remove the tag before attempting to delete this flag.</span>' : 'Remove feature'}
                                </Tooltip>
                            </Column>
                        ))}
                    </Permission>
                </Row>
            </Row>
        );
    }
}

export default TheComponent;
