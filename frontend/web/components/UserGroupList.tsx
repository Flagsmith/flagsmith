import React, { FC, useState } from 'react'
const CreateGroup = require('./modals/CreateGroup')
import Button from './base/forms/Button'
import AccountStore from 'common/stores/account-store'
import { UserGroup } from 'common/types/responses'
import {
  useDeleteGroupMutation,
  useGetGroupsQuery,
} from 'common/services/useGroup'
import PanelSearch from './PanelSearch'
import { sortBy } from 'lodash'
import InfoMessage from './InfoMessage' // we need this to make JSX compile
const Panel = require('components/base/grid/Panel')

type UserGroupsListType = {
  noTitle?: boolean
  orgId: string
  showRemove?: boolean
  onClick: (group: UserGroup) => void
  onEditPermissions?: (group: UserGroup) => void
}

const UserGroupsList: FC<UserGroupsListType> = ({
  noTitle,
  onClick,
  onEditPermissions,
  orgId,
  showRemove,
}) => {
  const [page, setPage] = useState(1)
  const { data: userGroups, isLoading } = useGetGroupsQuery({
    orgId: `${orgId}`,
    page,
  })
  const [deleteGroup] = useDeleteGroupMutation({})
  const isAdmin = AccountStore.isAdmin()

  const removeGroup = (id: number, name: string) => {
    openConfirm(
      <h3>Delete Group</h3>,
      <p>
        {'Are you sure you want to delete '}
        <strong>{name}</strong>
        {'?'}
      </p>,
      () => deleteGroup({ id, orgId }),
    )
  }

  return (
    <FormGroup>
      <InfoMessage>
        Group admins and users with the organisation permission{' '}
        <strong>Manage Groups</strong> can invite additional members to groups.
      </InfoMessage>
      <PanelSearch
        id='users-list'
        title={noTitle ? '' : 'Groups'}
        className='no-pad'
        itemHeight={64}
        icon='ion-md-people'
        items={sortBy(userGroups?.results, 'name')}
        paging={userGroups}
        nextPage={() => setPage(page + 1)}
        prevPage={() => setPage(page - 1)}
        goToPage={setPage}
        renderRow={(group: UserGroup, index: number) => {
          const { id, name, users } = group
          const _onClick = () => {
            if (onClick) {
              onClick(group)
            } else {
              openModal(
                'Edit Group',
                <CreateGroup isEdit orgId={orgId} group={group} />,
                'side-modal fade create-feature-modal',
              )
            }
          }
          return (
            <Row
              space
              className='list-item clickable'
              key={id}
              data-test={`user-item-${index}`}
            >
              <Flex onClick={_onClick}>
                <div>
                  <Button theme='text'>{name}</Button>
                </div>
                <div className='list-item-footer faint'>
                  {users.length}
                  {users.length === 1 ? ' Member' : ' Members'}
                </div>
              </Flex>

              {onEditPermissions && isAdmin && (
                <Button
                  theme="text"
                  onClick={() => onEditPermissions(group)}
                >
                  Edit Permissions
                </Button>
              )}
              {showRemove ? (
                <Column>
                  {isAdmin && (
                    <button
                      id='remove-group'
                      className='btn btn--with-icon'
                      type='button'
                      onClick={() => removeGroup(id, name)}
                    >
                      <RemoveIcon />
                    </button>
                  )}
                </Column>
              ) : (
                <span
                  onClick={_onClick}
                  style={{ fontSize: 24 }}
                  className='icon--primary ion ion-md-settings'
                />
              )}
            </Row>
          )
        }}
        isLoading={isLoading}
        renderNoResults={
          <Panel icon='ion-md-people' title={noTitle ? '' : 'Groups'}>
            <div className='p-2 text-center'>
              You have no groups in your organisation.
            </div>
          </Panel>
        }
      />
    </FormGroup>
  )
}

export default UserGroupsList
