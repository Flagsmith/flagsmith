import React, { FunctionComponent, Component } from 'react';
import TagValues from './TagValues';
import HistoryIcon from './HistoryIcon';
import ConfirmToggleFeature from './modals/ConfirmToggleFeature';
import ConfirmRemoveFeature from './modals/ConfirmRemoveFeature';
import CreateFlagModal from './modals/CreateFlag'; // we need this to make JSX compile


class TheComponent extends Component {
    state = {};


    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    confirmToggle = (projectFlag, environmentFlag, cb) => {
        openModal('Toggle Feature', <ConfirmToggleFeature
          environmentId={this.props.environmentId}
          projectFlag={projectFlag} environmentFlag={environmentFlag}
          cb={cb}
        />);
    }

    confirmRemove = (projectFlag, cb) => {
        openModal('Remove Feature', <ConfirmRemoveFeature
          environmentId={this.props.environmentId}
          projectFlag={projectFlag}
          cb={cb}
        />);
    }

    editFlag = (projectFlag, environmentFlag) => {
        API.trackEvent(Constants.events.VIEW_FEATURE);
        openModal(`Edit Feature: ${projectFlag.name}`, <CreateFlagModal
          isEdit
          router={this.context.router}
          environmentId={this.props.environmentId}
          projectId={this.props.projectId}
          projectFlag={projectFlag}
          environmentFlag={environmentFlag}
          flagId={environmentFlag.id}
        />, null, { className: 'side-modal fade' });
    };


    render() {
        const { projectId, isProtected, projectFlag, permission, environmentFlags } = this.props;
        const { name, id, enabled, created_date, description, type } = this.props.projectFlag;
        const readOnly = flagsmith.hasFeature('read_only_mode');

        return (
            <Row
              style={{ flexWrap: 'nowrap' }}
              className={this.props.canDelete ? 'list-item clickable' : 'list-item'} key={id} space
              data-test={`feature-item-${this.props.index}`}
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
                    Utils.renderWithPermission(permission, Constants.environmentPermissions('Admin'), (
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
