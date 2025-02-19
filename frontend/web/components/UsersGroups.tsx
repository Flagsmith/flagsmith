import React, { FC } from 'react'
import {
  useGetGroupsQuery,
  useUpdateGroupMutation,
} from 'common/services/useGroup'
import { sortBy } from 'lodash'
import { User, UserGroup, UserGroupSummary } from 'common/types/responses'
import Switch from './Switch'
import PanelSearch from './PanelSearch'
import ErrorMessage from './ErrorMessage'

type UsersGroupsType = {
  user: User
  orgId: number
}
const widths = [120]

const UsersGroups: FC<UsersGroupsType> = ({ orgId, user }) => {
  const { data, error: groupsError, isLoading } = useGetGroupsQuery({ orgId })
  const [updateGroup, { error: saveError, isLoading: isSaving }] =
    useUpdateGroupMutation({})
  const error = groupsError || saveError
  const onGroupsUpdated = (res: { error?: any }) => {
    if (res.error) {
      toast('Error updating group', 'danger')
    } else {
      toast('Updated user groups')
    }
  }
  return isLoading ? (
    <div className='text-center'>
      <Loader />
    </div>
  ) : (
    <>
      <ErrorMessage error={error} />
      <PanelSearch
        noResultsText={(search: string) =>
          search ? (
            <Flex className='text-center'>
              No results found for <strong>{search}</strong>
            </Flex>
          ) : (
            <Flex className='text-center'>This group has no members</Flex>
          )
        }
        id='org-members-list'
        title='Groups'
        className='no-pad overflow-visible'
        renderSearchWithNoResults
        items={sortBy(data?.results, 'name')}
        filterRow={(item: UserGroupSummary, search: string) => {
          const strToSearch = `${item.name} ${item.external_id}`
          return strToSearch.toLowerCase().indexOf(search.toLowerCase()) !== -1
        }}
        header={
          <>
            <Row className='table-header'>
              <Flex className='table-column px-3'>
                <div>Group</div>
              </Flex>
              <div className='table-column ml-1' style={{ width: widths[0] }}>
                Member
              </div>
              <div className='table-column ml-1' style={{ width: widths[1] }}>
                Admin
              </div>
            </Row>
          </>
        }
        renderRow={(group: UserGroup) => {
          const { external_id, id, name, users } = group
          const groupUser = users.find((v) => v.id === user.id)
          const isInGroup = !!groupUser
          const isAdmin = groupUser?.group_admin
          return (
            <Row className='list-item' key={id}>
              <Flex className='table-column px-3'>
                <div className='font-weight-medium'>{name}</div>
                <div className='text-muted'>{external_id}</div>
              </Flex>
              <div className='table-column' style={{ width: widths[0] }}>
                <Switch
                  disabled={isSaving}
                  checked={isInGroup}
                  onChange={(v: boolean) => {
                    if (v) {
                      updateGroup({
                        data: { ...group, users: group.users.concat([user]) },
                        orgId: `${orgId}`,
                        users: group.users.concat([user]),
                        usersToAddAdmin: null,
                        usersToRemove: null,
                        usersToRemoveAdmin: null,
                      }).then(onGroupsUpdated)
                    } else {
                      updateGroup({
                        data: group,
                        orgId: `${orgId}`,
                        users: group.users,
                        usersToAddAdmin: null,
                        usersToRemove: [user.id],
                        usersToRemoveAdmin: null,
                      }).then(onGroupsUpdated)
                    }
                  }}
                />
              </div>
              <div className='table-column' style={{ width: widths[1] }}>
                <Switch
                  disabled={isSaving}
                  checked={isAdmin}
                  onChange={(v: boolean) => {
                    if (v) {
                      updateGroup({
                        data: { ...group, users: group.users.concat([user]) },
                        orgId: `${orgId}`,
                        users: isInGroup
                          ? group.users
                          : group.users.concat([user]),
                        usersToAddAdmin: [user.id],
                        usersToRemove: null,
                        usersToRemoveAdmin: null,
                      }).then(onGroupsUpdated)
                    } else {
                      updateGroup({
                        data: group,
                        orgId: `${orgId}`,
                        users: group.users,
                        usersToAddAdmin: null,
                        usersToRemove: null,
                        usersToRemoveAdmin: [user.id],
                      }).then(onGroupsUpdated)
                    }
                  }}
                />
              </div>
            </Row>
          )
        }}
      />
    </>
  )
}

export default UsersGroups
