import React, {PureComponent, FC, Component, useEffect, useState} from 'react';
import Switch from './Switch';
import Tabs from './base/forms/Tabs';
import TabItem from './base/forms/TabItem';
import _data from '../../common/data/base/_data';
import UserGroupList from './UserGroupList';
import InfoMessage from './InfoMessage';
import {PermissionLevel} from "../../common/types/requests";
import {RouterChildContext} from "react-router";
import Button, {ButtonLink} from "./base/forms/Button";
import {User, UserGroup, UserPermission} from "../../common/types/responses";
const OrganisationProvider = require('../../common/providers/OrganisationProvider');
const AvailablePermissionsProvider = require('../../common/providers/AvailablePermissionsProvider');
const AppActions = require('../../common/dispatcher/app-actions');
const AccountStore = require('../../common/stores/account-store');
const Format = require('../../common/utils/format');
const Project = require('../../common/project');
const PanelSearch = require('./PanelSearch');

class _EditPermissionsModal extends Component {
  static displayName = 'EditPermissionsModal';

  static propTypes = {};

  constructor(props) {
      super(props);
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

                  if (!entityPermissions.admin && !(entityPermissions.permissions.find(v => v === (`VIEW_${this.props.parentLevel.toUpperCase()}`)))) {
                      this.state.parentError = true;
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

      return (

      );
  }
}


type EditPermissionModalType = {
    level: PermissionLevel
    isGroup?:boolean
    id: string
}

const _EditPermissionModal: FC<EditPermissionModalType> = ({level, isGroup}) => {
    const [entityPermissions, setEntityPermissions] = useState();


    const admin = () => entityPermissions && entityPermissions.admin

    const hasPermission = (key) => {
        if (admin()) return true;
        return entityPermissions.permissions.includes(key);
    }

    const close = () => {
        closeModal();
    }

    const save = () => {
        const id = typeof entityPermissions.id === 'undefined' ? '' : this.state.entityPermissions.id;
        const url = isGroup ? `${this.props.level}s/${this.props.id}/user-group-permissions/${id}`
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


    const isAdmin = this.admin();
    const hasRbacPermission = Utils.getPlansPermission('RBAC');


    return (
        <AvailablePermissionsProvider level={level}>
            {(props) => {
                const { permissions, isLoading } = props;
                return (isLoading || !permissions || !entityPermissions ? <div className="text-center"><Loader/></div>
                    : (
                        <div>
                            <div className="list-item">
                                {this.props.level !== 'organisation' && (
                                    <Row>
                                        <Flex>
                                            <bold>
                                                Administrator
                                            </bold>
                                            <div className="list-item-footer faint">
                                                {
                                                    hasRbacPermission ? `Full View and Write permissions for the given ${Format.camelCase(this.props.level)}.`
                                                        : (
                                                            <span>
                                                                Role-based access is not available on our Free Plan. Please visit <a href="https://flagsmith.com/pricing/">our Pricing Page</a> for more information on our licensing options.
                                                            </span>
                                                        )
                                                }
                                            </div>
                                        </Flex>
                                        <Switch disabled={!hasRbacPermission} onChange={this.toggleAdmin} checked={isAdmin}/>
                                    </Row>
                                )}

                            </div>
                            <div className="panel--grey">
                                <PanelSearch
                                    title="Permissions"
                                    className="no-pad"
                                    items={permissions}
                                    renderRow={(p) => {
                                        const levelUpperCase = this.props.level.toUpperCase();
                                        const disabled = this.props.level !== 'organisation' && p.key !== `VIEW_${levelUpperCase}` && !this.hasPermission(`VIEW_${levelUpperCase}`);
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

                            {
                                this.state.parentError && (
                                    <InfoMessage>
                                        The selected {this.props.isGroup ? 'group' : 'user'} does not have explicit user permissions to view this {this.props.parentLevel}. If the user does not belong to any groups with this permissions, you may have to adjust their permissions in <a onClick={() => {
                                        this.props.push(this.props.parentSettingsLink);
                                        closeModal();
                                    }}
                                    ><strong>{this.props.parentLevel} settings</strong>
                                    </a>.
                                    </InfoMessage>
                                )
                            }
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
    )
}

export default EditPermissionModal


export const EditPermissionsModal = ConfigProvider(_EditPermissionsModal);

type EditPermissionsType = {
    id: string
    isGroup?:boolean
    parentId?:string
    tabClassName?:string
    parentLevel?:string
    onSaveGroup?: ()=>void
    onSaveUser: ()=>void
    permissions?: UserPermission[]
    level: PermissionLevel
    parentSettingsLink?: string
    group?: {}
}

const EditPermissions: FC<EditPermissionsType> = (props) => {
    const [tab, setTab] = useState();

    useEffect(()=>{
        AppActions.getGroups(AccountStore.getOrganisation().id);
    },[])
    const editUserPermissions = (user:User) => {
        openModal(`Edit ${Format.camelCase(props.level)} Permissions`, <EditPermissionsModal
            name={`${user.first_name} ${user.last_name}`}
            id={props.id}
            onSave={props.onSaveUser}
            level={props.level}
            parentId={props.parentId}
            parentLevel={props.parentLevel}
            parentSettingsLink={props.parentSettingsLink}
            user={user}
            push={props.router.history.push}
        />);
    }

    const editGroupPermissions = (group:UserGroup) => {
        openModal(`Edit ${Format.camelCase(props.level)} Permissions`, <EditPermissionsModal
            name={`${group.name}`}
            id={props.id}
            isGroup
            onSave={props.onSaveGroup}
            level={props.level}
            parentId={props.parentId}
            parentLevel={props.parentLevel}
            parentSettingsLink={props.parentSettingsLink}
            group={group}
            push={props.router.history.push}
        />);
    }

    return (
        <div className="mt-4">
            <p>
                Flagsmith lets you manage fine-grained permissions for your projects and environments.
                {' '}
                <ButtonLink href="https://docs.flagsmith.com/advanced-use/permissions" target="_blank">Learn about User Roles.</ButtonLink>
            </p>
            <Tabs value={tab} onChange={setTab}>
                <TabItem tabLabel="Users">
                    <OrganisationProvider>
                        {({ isLoading, users }:{isLoading:boolean, users?:User[]}) => (
                            <div className="mt-4">
                                {isLoading && (!users?.length) && <div className="centered-container"><Loader/></div>}
                                {!!users?.length && (
                                    <div>
                                        <FormGroup className="panel no-pad pl-2 pr-2 panel--nested">
                                            <div className={props.tabClassName}>
                                                <PanelSearch
                                                    id="org-members-list"
                                                    title=""
                                                    className="panel--transparent"
                                                    items={users}
                                                    renderRow={({ id, first_name, last_name, email, role }:User) => {
                                                        const onClick = () => {
                                                            if (role !== 'ADMIN') {
                                                                editUserPermissions({ id, first_name, last_name, email, role });
                                                            }
                                                        };
                                                        const matchingPermissions = props.permissions?.find(v => v.user.id === id);

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
                                                                            matchingPermissions && matchingPermissions.admin ? `${Format.camelCase(props.level)} Administrator` : 'Regular User'
                                                                        }
                                                                        </span>
                                                                        <span style={{ fontSize: 24 }} className="icon--primary ion ion-md-settings"/>
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
                                                    filterRow={(item:User, search:string) => {
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
                    <FormGroup className="panel no-pad pl-2 mt-4 pr-2 panel--nested">
                        <div className={props.tabClassName}>
                            <UserGroupList noTitle orgId={AccountStore.getOrganisation().id} onClick={(group:UserGroup) => editGroupPermissions(group)}/>
                        </div>
                    </FormGroup>
                </TabItem>
            </Tabs>
        </div>
    )
}

export default ConfigProvider(EditPermissions);
