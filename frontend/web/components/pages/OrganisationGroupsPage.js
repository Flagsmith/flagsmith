import React, { Component } from 'react'
import UserGroupList from 'components/UserGroupList'
import CreateGroupModal from 'components/modals/CreateGroup'
import withAuditWebhooks from 'common/providers/withAuditWebhooks'
import Button from 'components/base/forms/Button'
import { EditPermissionsModal } from 'components/EditPermissions'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
import Permission from 'common/providers/Permission'

const OrganisationGroupsPage = class extends Component {
  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  static displayName = 'OrganisationGroupsPage'

  constructor(props, context) {
    super(props, context)
    this.state = {
      manageSubscriptionLoaded: true,
      role: 'ADMIN',
    }
    if (!AccountStore.getOrganisation()) {
      return
    }
    AppActions.getOrganisation(AccountStore.getOrganisation().id)
  }

  componentDidMount = () => {
    API.trackPage(Constants.pages.ORGANISATION_SETTINGS)
    $('body').trigger('click')
  }

  editGroupPermissions = (group) => {
    openModal(
      'Edit Organisation Permissions',
      <EditPermissionsModal
        name={`${group.name}`}
        id={AccountStore.getOrganisation().id}
        isGroup
        onSave={() => {
          AppActions.getOrganisation(AccountStore.getOrganisation().id)
        }}
        level='organisation'
        group={group}
        push={this.context.router.history.push}
      />,
      'p-0',
    )
  }

  render() {
    return (
      <div className='app-container container'>
        <AccountProvider onSave={this.onSave} onRemove={this.onRemove}>
          {({ organisation }, {}) =>
            !!organisation && (
              <div>
                <div>
                  <Row space className='mt-4'>
                    <h3 className='m-b-0'>User Groups</h3>
                    <Permission
                      level='organisation'
                      permission='MANAGE_USER_GROUPS'
                      id={AccountStore.getOrganisation().id}
                    >
                      {({ permission }) => (
                        <>
                          {Utils.renderWithPermission(
                            permission,
                            Constants.organisationPermissions('Manage Groups'),
                            <Button
                              className='mr-2'
                              id='btn-invite'
                              disabled={!permission}
                              onClick={() =>
                                openModal(
                                  'Create Group',
                                  <CreateGroupModal orgId={organisation.id} />,
                                )
                              }
                              type='button'
                            >
                              Create Group
                            </Button>,
                          )}
                        </>
                      )}
                    </Permission>
                  </Row>
                  <p>
                    Groups allow you to manage permissions for viewing and
                    editing projects, features and environments.
                  </p>
                  <UserGroupList
                    onEditPermissions={this.editGroupPermissions}
                    showRemove
                    orgId={organisation && organisation.id}
                  />
                </div>
              </div>
            )
          }
        </AccountProvider>
      </div>
    )
  }
}

OrganisationGroupsPage.propTypes = {}

module.exports = ConfigProvider(withAuditWebhooks(OrganisationGroupsPage))
