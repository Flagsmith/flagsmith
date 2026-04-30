import React from 'react'
import AppActions from 'common/dispatcher/app-actions'
import { Organisation, User } from 'common/types/responses'
import PanelSearch from 'components/PanelSearch'
import Format from 'common/utils/format'
import OrganisationUsersTableHeader from './components/OrganisationUsersTableHeader'
import OrganisationUsersTableRow from './components/OrganisationUsersTableRow'
import EditUserPermissionsModal from './components/EditUserPermissionsModal'
import InspectUserPermissionsModal from './components/InspectUserPermissionsModal'
import getUserDisplayName from 'common/utils/getUserDisplayName'
interface OrganisationUsersTableProps {
  users: User[]
  organisation: Organisation
  widths: number[]
}

const OrganisationUsersTable: React.FC<OrganisationUsersTableProps> = ({
  organisation,
  users,
  widths,
}) => {
  const editUserPermissions = (user: User, organisationId: number) => {
    openModal(
      user.first_name || user.last_name
        ? `${user.first_name} ${user.last_name}`
        : `${user.email}`,
      <EditUserPermissionsModal user={user} orgId={organisationId} />,
      'p-0 side-modal',
    )
  }

  const inspectPermissions = (user: User, organisationId: number) => {
    openModal(
      getUserDisplayName(user),
      <InspectUserPermissionsModal user={user} orgId={organisationId} />,
      'p-0 side-modal',
    )
  }

  const deleteUser = (id: number, userDisplayName: string) => {
    openConfirm({
      body: (
        <div>
          Are you sure you want to remove the user{' '}
          <strong>{userDisplayName}</strong> from the organisation? This action
          cannot be undone.
        </div>
      ),
      destructive: true,
      onYes: () => AppActions.deleteUser(id),
      title: 'Delete User',
      yesText: 'Confirm',
    })
  }

  return (
    <PanelSearch
      id='org-members-list'
      title='Members'
      className='no-pad'
      header={<OrganisationUsersTableHeader widths={widths} />}
      items={users}
      itemHeight={65}
      renderRow={(user) => {
        const { email, first_name, id, last_name } = user

        const onRemoveClick = () => {
          deleteUser(
            id,
            Format.userDisplayName({
              email,
              firstName: first_name,
              lastName: last_name,
            }),
          )
        }
        const onEditClick = () => {
          editUserPermissions(user, organisation.id)
        }

        return (
          <OrganisationUsersTableRow
            widths={widths}
            inspectPermissions={inspectPermissions}
            onEditClick={onEditClick}
            onRemoveClick={onRemoveClick}
            user={user}
            organisation={organisation}
          />
        )
      }}
      renderNoResults={<div>You have no users in this organisation.</div>}
      filterRow={(item: User, search: string) => {
        const strToSearch = `${item.first_name} ${item.last_name} ${item.email}`
        return strToSearch.toLowerCase().indexOf(search.toLowerCase()) !== -1
      }}
    />
  )
}

export default OrganisationUsersTable
