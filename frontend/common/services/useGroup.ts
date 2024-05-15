import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import { getStore } from 'common/store'
import Utils from 'common/utils/utils'

export const groupService = service
  .enhanceEndpoints({
    addTagTypes: ['Group', 'UserGroupPermission', 'GroupSummary'],
  })
  .injectEndpoints({
    endpoints: (builder) => ({
      createGroup: builder.mutation<Res['group'], Req['createGroup']>({
        invalidatesTags: [
          { id: 'LIST', type: 'Group' },
          { type: 'GroupSummary' },
        ],
        queryFn: async (query, { dispatch }, _, baseQuery) => {
          //Create the group
          const { data, error } = await baseQuery({
            body: query.data,
            method: 'POST',
            url: `organisations/${query.orgId}/groups/`,
          })
          if (error) {
            return { error }
          }
          //Add the members
          if (query.users?.length) {
            const { error } = await baseQuery({
              body: { user_ids: query.users.map((u) => u.id) },
              method: 'POST',
              url: `organisations/${query.orgId}/groups/${data.id}/`,
            })
          }
          // Make the admins
          await Promise.all(
            (query.usersToAddAdmin || []).map((v) =>
              createGroupAdmin(getStore(), {
                group: data.id,
                orgId: query.orgId,
                user: v,
              }),
            ),
          )
          return { data }
        },
      }),
      createGroupAdmin: builder.mutation<
        Res['groupAdmin'],
        Req['createGroupAdmin']
      >({
        invalidatesTags: [
          { id: 'LIST', type: 'Group' },
          { type: 'GroupSummary' },
        ],
        query: (query: Req['createGroupAdmin']) => ({
          body: {},
          method: 'POST',
          url: `organisations/${query.orgId}/groups/${query.group}/users/${query.user}/make-admin`,
        }),
      }),
      deleteGroup: builder.mutation<Res['groups'], Req['deleteGroup']>({
        invalidatesTags: [
          { id: 'LIST', type: 'Group' },
          { type: 'UserGroupPermission' },
          { type: 'GroupSummary' },
        ],
        query: (query: Req['deleteGroup']) => ({
          body: query,
          method: 'DELETE',
          url: `organisations/${query.orgId}/groups/${query.id}/`,
        }),
      }),
      deleteGroupAdmin: builder.mutation<
        Res['groupAdmin'],
        Req['deleteGroupAdmin']
      >({
        invalidatesTags: [
          { id: 'LIST', type: 'Group' },
          { type: 'GroupSummary' },
        ],
        query: (query: Req['deleteGroupAdmin']) => ({
          body: {},
          method: 'POST',
          url: `organisations/${query.orgId}/groups/${query.group}/users/${query.user}/remove-admin`,
        }),
      }),
      getGroup: builder.query<Res['group'], Req['getGroup']>({
        providesTags: (res) => [{ id: res?.id, type: 'Group' }],
        query: (query: Req['getGroup']) => ({
          url: `organisations/${query.orgId}/groups/${query.id}/`,
        }),
      }),
      getGroups: builder.query<Res['groups'], Req['getGroups']>({
        providesTags: [{ id: 'LIST', type: 'Group' }],
        query: ({ orgId, ...rest }) => ({
          url: `organisations/${orgId}/groups/?${Utils.toParam({ ...rest })}`,
        }),
      }),
      updateGroup: builder.mutation<Res['group'], Req['updateGroup']>({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'Group' },
          { id: res?.id, type: 'Group' },
          { type: 'GroupSummary' },
        ],
        queryFn: async (query, { dispatch }, _, baseQuery) => {
          //Create the group
          const { data, error } = await baseQuery({
            body: query.data,
            method: 'PUT',
            url: `organisations/${query.orgId}/groups/${query.data.id}/`,
          })
          if (error) {
            return { error }
          }
          //Add the members
          if (query.users?.length) {
            await baseQuery({
              body: { user_ids: query.data.users.map((u) => u.id) },
              method: 'POST',
              url: `organisations/${query.orgId}/groups/${data.id}/add-users/`,
            })
          }
          if (query.usersToRemove?.length) {
            await baseQuery({
              body: { user_ids: query.usersToRemove },
              method: 'POST',
              url: `organisations/${query.orgId}/groups/${data.id}/remove-users/`,
            })
          }
          // Make the admins
          await Promise.all(
            (query.usersToAddAdmin || []).map((v) =>
              createGroupAdmin(getStore(), {
                group: data.id,
                orgId: query.orgId,
                user: v,
              }),
            ),
          )

          await Promise.all(
            (query.usersToRemoveAdmin || []).map((v) =>
              deleteGroupAdmin(getStore(), {
                group: data.id,
                orgId: query.orgId,
                user: v,
              }),
            ),
          )
          return { data }
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getGroups(
  store: any,
  data: Req['getGroups'],
  options?: Parameters<typeof groupService.endpoints.getGroups.initiate>[1],
) {
  return store.dispatch(
    groupService.endpoints.getGroups.initiate(data, options),
  )
}

export async function createGroupAdmin(
  store: any,
  data: Req['createGroupAdmin'],
  options?: Parameters<
    typeof groupService.endpoints.createGroupAdmin.initiate
  >[1],
) {
  return store.dispatch(
    groupService.endpoints.createGroupAdmin.initiate(data, options),
  )
}
export async function deleteGroupAdmin(
  store: any,
  data: Req['deleteGroupAdmin'],
  options?: Parameters<
    typeof groupService.endpoints.deleteGroupAdmin.initiate
  >[1],
) {
  return store.dispatch(
    groupService.endpoints.deleteGroupAdmin.initiate(data, options),
  )
}
export async function deleteGroup(
  store: any,
  data: Req['deleteGroup'],
  options?: Parameters<typeof groupService.endpoints.deleteGroup.initiate>[1],
) {
  return store.dispatch(
    groupService.endpoints.deleteGroup.initiate(data, options),
  )
}
export async function getGroup(
  store: any,
  data: Req['getGroup'],
  options?: Parameters<typeof groupService.endpoints.getGroup.initiate>[1],
) {
  return store.dispatch(groupService.endpoints.getGroup.initiate(data, options))
}
export async function createGroup(
  store: any,
  data: Req['createGroup'],
  options?: Parameters<typeof groupService.endpoints.createGroup.initiate>[1],
) {
  return store.dispatch(
    groupService.endpoints.createGroup.initiate(data, options),
  )
}
export async function updateGroup(
  store: any,
  data: Req['updateGroup'],
  options?: Parameters<typeof groupService.endpoints.updateGroup.initiate>[1],
) {
  return store.dispatch(
    groupService.endpoints.updateGroup.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateGroupAdminMutation,
  useCreateGroupMutation,
  useDeleteGroupAdminMutation,
  useDeleteGroupMutation,
  useGetGroupQuery,
  useGetGroupsQuery,
  useUpdateGroupMutation,
  // END OF EXPORTS
} = groupService

/* Usage examples:
const { data, isLoading } = useGetGroupsQuery({ id: 2 }, {}) //get hook
const [createGroups, { isLoading, data, isSuccess }] = useCreateGroupsMutation() //create hook
groupService.endpoints.getGroups.select({id: 2})(store.getState()) //access data from any function
*/
