// import propTypes from 'prop-types';
import React, { PureComponent } from 'react';
import UserGroupsProvider from '../../common/providers/UserGroupsProvider';
import CreateGroup from './modals/CreateGroup';
import Button from './base/forms/Button';

export default class TheComponent extends PureComponent {
  static displayName = 'TheComponent';

  static propTypes = {};

  constructor(props) {
      super(props);
      this.state = {};
  }

  componentDidMount() {
      AppActions.getGroups(this.props.orgId);
  }

  componentWillUpdate(nextProps, nextState, nextContext) {
      if (nextProps.orgId !== this.props.orgId) {
          AppActions.getGroups(nextProps.orgId);
      }
  }


  removeGroup = (id, name) => {
      openConfirm(
          <h3>Delete Group</h3>,
          <p>
              {'Are you sure you want to delete '}
              <strong>{name}</strong>
              {'?'}
          </p>,
          () => AppActions.deleteGroup(this.props.orgId, id),
      );
  }


  render() {
      // const { props } = this;
      return (
          <UserGroupsProvider>
              {({ isLoading, userGroups, userGroupsPaging }) => (
                  <FormGroup>
                      <PanelSearch
                        renderSearchWithNoResults
                        id="users-list"
                        title={this.props.noTitle ? '' : 'Groups'}
                        className="no-pad"
                        itemHeight={64}
                        icon="ion-md-people"
                        items={userGroups}
                        paging={userGroupsPaging}
                        nextPage={() => AppActions.getGroupsPage(this.props.orgId, userGroupsPaging.next)}
                        prevPage={() => AppActions.getGroupsPage(this.props.orgId, userGroupsPaging.previous)}
                        goToPage={page => AppActions.getGroupsPage(this.props.orgId, `${Project.api}organisations/${this.props.orgId}/groups/?page=${page}`)}
                        renderRow={(group, index) => {
                            const { id, name, users } = group;
                            const onClick = () => {
                                if (this.props.onClick) {
                                    this.props.onClick(group);
                                } else {
                                    openModal('Edit Group', <CreateGroup orgId={this.props.orgId} group={{ id, users, name }}/>);
                                }
                            };
                            return (
                                <Row
                                  space className="list-item clickable" key={id}
                                  data-test={`user-item-${index}`}
                                >
                                    <Flex
                                      onClick={onClick}

                                    >
                                        <div>
                                            <ButtonLink>
                                                {name}
                                            </ButtonLink>
                                        </div>
                                        <div className="list-item-footer faint">
                                            {users.length}{users.length == 1 ? ' Member' : ' Members'}
                                        </div>
                                    </Flex>

                                    {this.props.onEditPermissions && (
                                        <Button onClick={() => this.props.onEditPermissions(group)} className="btn--link">Edit Permissions</Button>
                                    )}
                                    {this.props.showRemove ? (
                                        <Column>
                                            <button
                                              id="remove-group"
                                              className="btn btn--with-icon"
                                              type="button"
                                              onClick={() => this.removeGroup(id, name)}
                                            >
                                                <RemoveIcon/>
                                            </button>
                                        </Column>
                                    ) : (
                                        <ion onClick={onClick} style={{ fontSize: 24 }} className="icon--primary ion ion-md-settings"/>

                                    )}

                                </Row>
                            );
                        }}
                        renderNoResults={(
                            <FormGroup className="text-center pb-4">
                                      You have no groups in your organisation.
                            </FormGroup>
                )}
                        isLoading={isLoading}
                      />
                  </FormGroup>
              )}

          </UserGroupsProvider>
      );
  }
}
