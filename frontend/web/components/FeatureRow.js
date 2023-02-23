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
        const { feature, tab } = Utils.fromParam();
        const { id } = projectFlag;
        if (`${id}` === feature) {
            this.editFeature(projectFlag, environmentFlags[id], tab);
        }
    }

    confirmRemove = (projectFlag, cb) => {
        openModal('Remove Feature', <ConfirmRemoveFeature
          environmentId={this.props.environmentId}
          projectFlag={projectFlag}
          cb={cb}
        />);
    }

    editFeature = (projectFlag, environmentFlag, tab) => {
        API.trackEvent(Constants.events.VIEW_FEATURE);

        history.replaceState(
            {},
            null,
            `${document.location.pathname}?feature=${projectFlag.id}${tab ? `&tab=${tab}` : ''}`,
        );
        openModal(`${this.props.permission ? 'Edit Feature' : 'Feature'}: ${projectFlag.name}`, <CreateFlagModal
          isEdit
          router={this.context.router}
          environmentId={this.props.environmentId}
          projectId={this.props.projectId}
          projectFlag={projectFlag}
          noPermissions={!this.props.permission}
          environmentFlag={environmentFlag}
          flagId={environmentFlag.id}
        />, null, { className: 'side-modal fade create-feature-modal',
            onClose: () => {
                history.replaceState(
                    {},
                    null,
                    `${document.location.pathname}`,
                );
            } });
    };


    render() {
        const { projectId, projectFlag, permission, environmentFlags, environmentId, projectFlags, removeFlag, toggleFlag } = this.props;
        const { name, id, created_date, description } = this.props.projectFlag;
        const readOnly = this.props.readOnly || Utils.getFlagsmithHasFeature('read_only_mode');
        const isProtected = TagStore.hasProtectedTag(projectFlag, parseInt(projectId));
        const environment = ProjectStore.getEnvironment(environmentId);
        const changeRequestsEnabled = Utils.changeRequestsEnabled(environment && environment.minimum_change_request_approvals);

        if (this.props.condensed) {
            return (
                <Row
                  onClick={() => !readOnly && this.editFeature(projectFlag, environmentFlags[id])}
                  style={{ overflow: 'hidden', ...(this.props.style || {}) }}
                >
                    <div className={`mr-2 ${this.props.fadeEnabled && 'faded'}`}>
                        <Switch
                          disabled={!permission || readOnly}
                          data-test={`feature-switch-${this.props.index}${environmentFlags[id] && environmentFlags[id].enabled ? '-on' : '-off'}`}
                          checked={environmentFlags[id] && environmentFlags[id].enabled}
                          onChange={() => {
                              if (changeRequestsEnabled) {
                                  this.editFeature(projectFlag, environmentFlags[id]);
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
                          onClick={() => permission && !readOnly && this.editFeature(projectFlag, environmentFlags[id])}
                          value={environmentFlags[id] && environmentFlags[id].feature_state_value}
                          data-test={`feature-value-${this.props.index}`}
                        />
                    </div>
                </Row>
            );
        }

        return (
            <Row
              style={{ flexWrap: 'nowrap' }}
              className={`list-item ${readOnly?"":"clickable"} ${this.props.widget?"py-1":"py-2"}`} key={id} space
              data-test={`feature-item-${this.props.index}`}
            >
                <div
                  className="flex flex-1"
                  onClick={() => !readOnly && this.editFeature(projectFlag, environmentFlags[id])}
                >
                    <div>
                        <Row>
                            <ButtonLink className={`mr-2 ${readOnly?"cursor-default":""}`}>
                                {name}
                            </ButtonLink>
                            {projectFlag.owners && !!projectFlag.owners.length ? (
                                <Tooltip
                                    title={(
                                        <ButtonLink>
                                            <span className="ion ion-md-person pr-2"/>
                                        </ButtonLink>
                                    )}
                                    place="right"
                                >
                                    {`Flag assigned to ${projectFlag.owners.map(v => `${v.first_name} ${v.last_name}`).join(', ')}`}
                                </Tooltip>

                            ) : (
                                <span/>
                            )}
                            <TagValues projectId={projectId} value={projectFlag.tags}/>

                        </Row>
                        <span className="text-small text-muted">
                            Created {moment(created_date).format('Do MMM YYYY HH:mma')}{' - '}
                            {description || 'No description'}
                        </span>
                    </div>

                </div>
                <Row>
                    <Row style={{
                        marginTop: 5,
                        marginBottom: 5,
                        marginRight: 15,
                    }}
                    >
                        <Column>
                            <FeatureValue
                              onClick={() => !readOnly && this.editFeature(projectFlag, environmentFlags[id])}
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
                                      this.editFeature(projectFlag, environmentFlags[id]);
                                      return;
                                  }
                                  this.confirmToggle(projectFlag, environmentFlags[id], (environments) => {
                                      toggleFlag(_.findIndex(projectFlags, { id }), environments);
                                  });
                              }}
                            />
                        </Column>
                    </Row>

                    {AccountStore.getOrganisationRole() === 'ADMIN' && !this.props.hideAudit && (
                    <Tooltip
                      html
                      title={(
                          <button
                            onClick={() => {
                                this.context.router.history.push(`/project/${projectId}/environment/${environmentId}/audit-log?env=${environment.id}&search=${projectFlag.name}`);
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
                    {!this.props.hideRemove && (
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
                                        {isProtected ? '<span>This feature has been tagged as <bold>protected</bold>, <bold>permanent</bold>, <bold>do not delete</bold>, or <bold>read only</bold>. Please remove the tag before attempting to delete this flag.</span>' : 'Remove feature'}
                                    </Tooltip>
                                </Column>
                            ))}
                        </Permission>
                    )}

                </Row>
            </Row>
        );
    }
}

export default TheComponent;
