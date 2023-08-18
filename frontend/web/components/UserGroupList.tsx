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
import Icon from './Icon'
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
      'Delete Group',
      <div>
        {'Are you sure you want to delete '}
        <strong>{name}</strong>
        {'?'}
      </div>,
      () => deleteGroup({ id, orgId }),
    )
  }

  return (
    <FormGroup>
      <div className='col-md-6'>
        <InfoMessage>
          Group admins and users with the organisation permission{' '}
          <strong>Manage Groups</strong> can invite additional members to
          groups.
        </InfoMessage>
      </div>
      <PanelSearch
        id='users-list'
        title={noTitle ? '' : 'Groups'}
        className='no-pad'
        itemHeight={64}
        items={sortBy(userGroups?.results, 'name')}
        paging={userGroups}
        nextPage={() => setPage(page + 1)}
        prevPage={() => setPage(page - 1)}
        goToPage={setPage}
        header={
          showRemove && (
            <Row className='table-header'>
              <Flex className='table-column px-3'>Groups</Flex>
              <div style={{ width: '170px' }} className='table-column'>
                Action
              </div>
              <div
                style={{ width: '80px' }}
                className='table-column text-center'
              >
                Remove
              </div>
            </Row>
          )
        }
        renderRow={(group: UserGroup, index: number) => {
          const { id, name, users } = group
          const _onClick = () => {
            if (onClick) {
              onClick(group)
            } else {
              openModal(
                'Edit Group',
                <CreateGroup isEdit orgId={orgId} group={group} />,
                'side-modal create-feature-modal',
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
              <Flex onClick={_onClick} className=' table-column px-3'>
                <div className='mb-1 font-weight-medium'>{name}</div>
                <div className='list-item-subtitle faint'>
                  {users.length}
                  {users.length === 1 ? ' Member' : ' Members'}
                </div>
              </Flex>

              {onEditPermissions && isAdmin ? (
                <div
                  style={{
                    width: '170px',
                  }}
                  onClick={() => onEditPermissions(group)}
                  className='table-column'
                >
                  <Button theme='text' size='small'>
                    <Icon name='edit' width={18} fill='#6837FC' /> Edit
                    Permissions
                  </Button>
                </div>
              ) : (
                <div style={{ width: '170px' }} className='table-column'></div>
              )}
              {showRemove ? (
                <div
                  style={{ width: '80px' }}
                  className='table-column text-center'
                >
                  {isAdmin && (
                    <Button
                      id='remove-group'
                      type='button'
                      onClick={() => removeGroup(id, name)}
                      className='btn btn-with-icon'
                    >
                      <Icon name='trash-2' width={20} fill='#656D7B' />
                    </Button>
                  )}
                </div>
              ) : (
                <div
                  onClick={_onClick}
                  style={{ width: '72px' }}
                  className='px-3 text-center'
                >
                  <Icon name='setting' width={20} fill='#656D7B' />
                </div>
              )}
            </Row>
          )
        }}
        isLoading={isLoading}
        renderNoResults={
          <Panel title={noTitle ? '' : 'Groups'} className='no-pad'>
            <div className='search-list'>
              <Row className='list-item p-3 text-muted'>
                You have no groups in your organisation.
              </Row>
            </div>
          </Panel>
        }
      />
    </FormGroup>
  )
}

export default UserGroupsList
