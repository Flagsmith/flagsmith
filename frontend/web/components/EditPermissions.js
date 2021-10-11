// import propTypes from 'prop-types';
import React, { PureComponent, Component } from 'react';
import Switch from './Switch';
import Tabs from './base/forms/Tabs';
import TabItem from './base/forms/TabItem';
import AvailablePermissionsProvider from '../../common/providers/AvailablePermissionsProvider';
import _data from '../../common/data/base/_data';
import UserGroupList from './UserGroupList';
// import propTypes from 'prop-types';

class _EditPermissionsModal extends Component {
  static displayName = 'EditPermissionsModal';

  static propTypes = {};

  constructor(props) {
      super(props);
      AppActions.getAvailablePermissions();
      let parentGet = Promise.resolve();
      if (this.props.parentLevel) {
          const parentUrl = props.isGroup ? `${props.parentLevel}s/${props.parentId}/user-group-permissions/` : `${props.parentLevel}s/${props.parentId}/user-permissions/`;

          parentGet = _data.get(`${Project.api}${parentUrl}`)
              .then((results) => {
                  let entityPermissions = props.isGroup ? _.find(results, r => r.group.id === props.group.id) : _.find(results, r => r.user.id === props.user.id);
                  if (!entityPermissions) {
                      entityPermissions = { admin: false, permissions: [] };
                  }
                  if (this.props.user) {
                      entityPermissions.user = this.props.user.id;
                  }
                  if (this.props.group) {
                      entityPermissions.group = this.props.group.id;
                  }

                  if (!entityPermissions.admin && !entityPermissions.permissions.length) {
                      throw 'Error';
                  }
              });
      }
      parentGet.then(() => {
          const url = props.isGroup ? `${props.level}s/${props.id}/user-group-permissions/` : `${props.level}s/${props.id}/user-permissions/`;
          _data.get(`${Project.api}${url}`)
              .then((results) => {
                  let entityPermissions = props.isGroup ? _.find(results, r => r.group.id === props.group.id) : _.find(results, r => r.user.id === props.user.id);
                  if (!entityPermissions) {
                      entityPermissions = { admin: false, permissions: [] };
                  }
                  if (this.props.user) {
                      entityPermissions.user = this.props.user.id;
                  }
                  if (this.props.group) {
                      entityPermissions.group = this.props.group.id;
                  }
                  this.setState({ entityPermissions });
              });
      }).catch(() => {
          this.setState({ parentError: true });
      });

      this.state = {};
  }

  admin = () => this.state.entityPermissions && this.state.entityPermissions.admin

  hasPermission = (key) => {
      if (this.admin()) return true;
      return this.state.entityPermissions.permissions.includes(key);
  }

  close = () => {
      closeModal();
  }

  save = () => {
      const id = typeof this.state.entityPermissions.id === 'undefined' ? '' : this.state.entityPermissions.id;
      const url = this.props.isGroup ? `${this.props.level}s/${this.props.id}/user-group-permissions/${id}`
          : `${this.props.level}s/${this.props.id}/user-permissions/${id}`;
      this.setState({ isSaving: true });
      const action = id ? 'put' : 'post';
      _data[action](`${Project.api}${url}${id && '/'}`, this.state.entityPermissions)
          .then(() => {
              this.props.onSave && this.props.onSave();
              this.close();
          })
          .catch((e) => {
              this.setState({ isSaving: false, error: e });
          });
  }

  togglePermission = (key) => {
      const index = this.state.entityPermissions.permissions.indexOf(key);
      if (index === -1) {
          this.state.entityPermissions.permissions.push(key);
      } else {
          this.state.entityPermissions.permissions.splice(index, 1);
      }
      this.forceUpdate();
  }

  toggleAdmin = (p) => {
      this.state.entityPermissions.admin = !this.state.entityPermissions.admin;
      this.forceUpdate();
  }

  render() {
      const {
          props: {
              level,
          },
          state: {
              entityPermissions,
              isSaving,
          },
      } = this;
      const isAdmin = this.admin();
      const hasRbacPermission = !this.props.hasFeature('plan_based_access') || Utils.getPlansPermission(AccountStore.getPlans(), 'RBAC');

      return (
          <AvailablePermissionsProvider level={level}>
              {(props) => {
                  const { permissions, isLoading } = props;
                  if (this.state.parentError) {
                      return (
                          <div>
                              The selected {this.props.isGroup ? 'group' : 'user'} does not have permission to view this {this.props.parentLevel}. Please adjust their permissions in <a onClick={() => {
                              this.props.push(this.props.parentSettingsLink);
                              closeModal()
                          }}
                              ><strong>{this.props.parentLevel} settings</strong>
                              </a>.
                          </div>
                      );
                  }
                  return (isLoading || !permissions || !entityPermissions ? <div className="text-center"><Loader/></div>
                      : (
                          <div>
                              <div className="list-item">
                                  <Row>
                                      <Flex>
                                          <bold>
                                              Administrator
                                          </bold>
                                          <div className="list-item-footer faint">
                                              {
                                              hasRbacPermission ? `Full View and Write permissions for the given ${Format.camelCase(this.props.level)}.`
                                                  : 'Please upgrade your account to enable role based access.'
                                            }
                                          </div>
                                      </Flex>
                                      <Switch disabled={!hasRbacPermission} onChange={this.toggleAdmin} checked={isAdmin}/>
                                  </Row>
                              </div>
                              <div className="panel--grey">
                                  <PanelSearch
                                    title="Permissions"
                                    className="no-pad"
                                    items={permissions}
                                    renderRow={(p) => {
                                        const disabled = this.props.level === 'project' && p.key !== 'VIEW_PROJECT' && !this.hasPermission('VIEW_PROJECT');
                                        return (
                                            <div key={p.key} style={this.admin() ? { opacity: 0.5 } : null} className="list-item">
                                                <Row>
                                                    <Flex>
                                                        <bold>
                                                            {Format.enumeration.get(p.key)}
                                                        </bold>
                                                        <div className="list-item-footer faint">
                                                            {p.description}
                                                        </div>
                                                    </Flex>
                                                    <Switch onChange={() => this.togglePermission(p.key)} disabled={disabled || this.admin() || !hasRbacPermission} checked={!disabled && this.hasPermission(p.key)}/>
                                                </Row>
                                            </div>
                                        );
                                    }}
                                  />
                              </div>

                              <p className="text-right mt-2">
                                This will edit the permissions for <bold>{this.props.isGroup ? `the ${this.props.name} group` : ` ${this.props.name}`}</bold>.
                              </p>
                              <div className="text-right">
                                  <Button
                                    onClick={this.save} data-test="update-feature-btn" id="update-feature-btn"
                                    disabled={isSaving || !hasRbacPermission}
                                  >
                                      {isSaving ? 'Saving' : 'Save'}
                                  </Button>
                              </div>
                          </div>
                      ));
              } }
          </AvailablePermissionsProvider>
      );
  }
}

const EditPermissionsModal = ConfigProvider(_EditPermissionsModal);

export default class EditPermissions extends PureComponent {
  static displayName = 'EditPermissions';

  static propTypes = {};

    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    constructor(props) {
        super(props);
        this.state = { tab: 0 };
        AppActions.getGroups(AccountStore.getOrganisation().id);
    }

  editUserPermissions = (user) => {
      openModal(`Edit ${Format.camelCase(this.props.level)} Permissions`, <EditPermissionsModal
        name={`${user.first_name} ${user.last_name}`}
        id={this.props.id}
        onSave={this.props.onSaveUser}
        level={this.props.level}
        parentId={this.props.parentId}
        parentLevel={this.props.parentLevel}
        parentSettingsLink={this.props.parentSettingsLink}
        user={user}
        push={this.context.router.history.push}
      />);
  }

  editGroupPermissions = (group) => {
      openModal(`Edit ${Format.camelCase(this.props.level)} Permissions`, <EditPermissionsModal
        name={`${group.name}`}
        id={this.props.id}
        isGroup
        onSave={this.props.onSaveGroup}
        level={this.props.level}
        parentId={this.props.parentId}
        parentLevel={this.props.parentLevel}
        parentSettingsLink={this.props.parentSettingsLink}
        group={group}
        push={this.context.router.history.push}
      />);
  }

  render() {
      // const { props } = this;
      return (
          <div className="mt-5">
              <h3>
                Manage Permissions
              </h3>
              <p>
                  Flagsmith lets you manage fine-grained permissions for your projects and environments.
                  {' '}
                  <ButtonLink href="https://docs.flagsmith.com/advanced-use/permissions" target="_blank">Learn about User Roles.</ButtonLink>
              </p>
              <Tabs value={this.state.tab} onChange={tab => this.setState({ tab })}>
                  <TabItem tabLabel="Users">
                      <OrganisationProvider>
                          {({ isLoading, name, projects, usage, users, invites }) => (
                              <div>
                                  {isLoading && (!users || !users.length) && <div className="centered-container"><Loader/></div>}
                                  {(users && users.length) && (
                                  <div>
                                      <FormGroup className="panel no-pad pl-2 pr-2 panel--nested">
                                          <div className={this.props.tabClassName}>
                                              <PanelSearch
                                                id="org-members-list"
                                                title=""
                                                className="panel--transparent"
                                                items={users}
                                                renderRow={({ id, first_name, last_name, email, role }) => {
                                                    const onClick = () => {
                                                        if (role !== 'ADMIN') {
                                                            this.editUserPermissions({ id, first_name, last_name, email, role });
                                                        }
                                                    };
                                                    const matchingPermissions = this.props.permissions && this.props.permissions.find(v => v.user.id === id);

                                                    return (
                                                        <Row
                                                          onClick={onClick} space className={`list-item${role === 'ADMIN' ? '' : ' clickable'}`}
                                                          key={id}
                                                        >
                                                            <div>
                                                                <strong>
                                                                    {`${first_name} ${last_name}`}
                                                                </strong>
                                                                {' '}
                                                                {id == AccountStore.getUserId() && '(You)'}
                                                                <div className="list-item-footer faint">
                                                                    {email}
                                                                </div>
                                                            </div>
                                                            {role === 'ADMIN' ? (
                                                                <Tooltip html title="Organisation Administrator">
                                                                    {'Organisation administrators have all permissions enabled.<br/>To change the role of this user, visit Organisation Settings.'}
                                                                </Tooltip>
                                                            ) : (
                                                                <div onClick={onClick} className="flex-row">
                                                                    <span className="mr-3">{
                                                                        matchingPermissions && matchingPermissions.admin ? `${Format.camelCase(this.props.level)} Administrator` : 'Regular User'
                                                                    }
                                                                    </span>
                                                                    <ion style={{ fontSize: 24 }} className="icon--primary ion ion-md-settings"/>
                                                                </div>
                                                            )}
                                                        </Row>
                                                    );
                                                }}
                                                renderNoResults={(
                                                    <div>
                                                You have no users in this organisation.
                                                    </div>
                                            )}
                                                filterRow={(item, search) => {
                                                    const strToSearch = `${item.first_name} ${item.last_name} ${item.email}`;
                                                    return strToSearch.toLowerCase().indexOf(search.toLowerCase()) !== -1;
                                                }}
                                              />
                                          </div>

                                          <div id="select-portal"/>
                                      </FormGroup>
                                  </div>
                                  )}
                              </div>
                          )}
                      </OrganisationProvider>
                  </TabItem>
                  <TabItem tabLabel="Groups">
                      <FormGroup className="panel no-pad pl-2 pr-2 panel--nested">
                          <div className={this.props.tabClassName}>
                              <UserGroupList noTitle orgId={AccountStore.getOrganisation().id} onClick={group => this.editGroupPermissions(group)}/>
                          </div>
                      </FormGroup>
                  </TabItem>
              </Tabs>
          </div>
      );
  }
}
