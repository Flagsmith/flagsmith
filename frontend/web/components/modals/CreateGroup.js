import React, { Component } from 'react';
import Switch from '../Switch';
import UserGroupsProvider from '../../../common/providers/UserGroupsProvider';
import data from '../../../common/data/base/_data';

const CreateGroup = class extends Component {
    static displayName = 'CreateGroup'

    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    constructor(props, context) {
        super(props, context);
        this.state = {
            name: props.group ? props.group.name : '',
            users: props.group ? props.group.users : [],
        };
    }

    close() {
        closeModal();
    }


    componentDidMount = () => {
        if (!this.props.isEdit && !E2E) {
            this.focusTimeout = setTimeout(() => {
                this.input.focus();
                this.focusTimeout = null;
            }, 500);
        }
    };

    componentWillUnmount() {
        if (this.focusTimeout) {
            clearTimeout(this.focusTimeout);
        }
    }

    getUsersToRemove = (users) => {
        return _.filter(users, ({id})=>{
            return !_.find(this.state.users, {id})
        })
    }

    save = (allUsers) => {
        const { name, users } = this.state;
        if (this.props.group) {
            AppActions.updateGroup(this.props.orgId, {
                id: this.props.group.id,
                name,
                users,
                usersToRemove: this.getUsersToRemove(allUsers),
            });
        } else {
            AppActions.createGroup(this.props.orgId, {
                name,
                users,
                usersToRemove: this.getUsersToRemove(allUsers),
            });
        }
    }

    toggleUser = (id) => {
        const isMember = _.find(this.state.users, { id });
        const users = _.filter(this.state.users, u => u.id !== id);
        this.setState({ users: isMember ? users : users.concat([{ id }]) });
    }

    render() {
        const { name } = this.state;
        const isEdit = !!this.props.group;
        return (

            <OrganisationProvider>
                {({ users }) => (
                    <UserGroupsProvider onSave={this.close}>
                        {({ isSaving }) => (
                            <form
                              id="create-feature-modal"
                              onSubmit={(e) => {
                                  Utils.preventDefault(e);
                                  this.save(users);
                              }}
                            >
                                <InputGroup
                                  title="Group name"
                                  ref={e => this.input = e}
                                  data-test="groupName"
                                  inputProps={{
                                      className: 'full-width',
                                      name: 'groupName',
                                  }}
                                  value={name}
                                  onChange={e => this.setState({ name: Utils.safeParseEventValue(e) })}
                                  isValid={name && name.length}
                                  type="text"
                                  name="Name*"
                                  placeholder="E.g. Developers"
                                />
                                <div className="mb-5">
                                    <PanelSearch
                                      id="org-members-list"
                                      title="Members"
                                      className="mt-5 no-pad"
                                      items={users}
                                      filterRow={(item, search) => {
                                          const strToSearch = `${item.first_name} ${item.last_name} ${item.id}`;
                                          return strToSearch.toLowerCase().indexOf(search.toLowerCase()) !== -1;
                                      }}
                                      renderRow={({ id, first_name, last_name, email }) => (
                                          <Row space className="list-item" key={id}>
                                              <div>
                                                  {`${first_name} ${last_name}`}
                                                  {' '}
                                                  {id == AccountStore.getUserId() && '(You)'}
                                                  <div className="list-item-footer faint">
                                                      {email}
                                                  </div>
                                              </div>
                                              <Switch onChange={() => this.toggleUser(id)} checked={!!_.find(this.state.users, { id })}/>
                                          </Row>
                                      )}
                                    />
                                </div>
                                <div className="text-right">
                                    {isEdit ? (
                                        <Button data-test="update-feature-btn" id="update-feature-btn" disabled={isSaving || !name}>
                                            {isSaving ? 'Updating' : 'Update Group'}
                                        </Button>
                                    ) : (
                                        <Button data-test="create-feature-btn" id="create-feature-btn" disabled={isSaving || !name}>
                                            {isSaving ? 'Creating' : 'Create Group'}
                                        </Button>
                                    )}
                                </div>
                            </form>
                        )}
                    </UserGroupsProvider>
                )}
            </OrganisationProvider>

        );
    }
};

CreateGroup.propTypes = {};

module.exports = ConfigProvider(CreateGroup);
