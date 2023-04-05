import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const groupService = service
  .enhanceEndpoints({ addTagTypes: ['Group'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createGroupAdmin: builder.mutation<
        Res['groupAdmin'],
        Req['createGroupAdmin']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'Group' }],
        query: (query: Req['createGroupAdmin']) => ({
          body: query,
          method: 'POST',
          url: `organisations/${query.orgId}/groups/${query.id}/users/:userId/make-admin`,
        }),
      }),
      deleteGroup: builder.mutation<Res['groups'], Req['deleteGroup']>({
        invalidatesTags: [{ id: 'LIST', type: 'Group' }],
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
        invalidatesTags: [{ id: 'LIST', type: 'Group' }],
        query: (query: Req['deleteGroupAdmin']) => ({
          body: query,
          method: 'DELETE',
          url: `organisations/${query.orgId}/groups/${query.id}/users/${query.userId}/remove-admin`,
        }),
      }),
      getGroups: builder.query<Res['groups'], Req['getGroups']>({
        providesTags: [{ id: 'LIST', type: 'Group' }],
        query: (query) => ({
          url: `organisations/${query.orgId}/groups/?page=${query.page}`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getGroups(
  store: any,
  data: Req['getGroups'],
  options?: Parameters<typeof groupService.endpoints.getGroups.initiate>[1],
) {
  store.dispatch(groupService.endpoints.getGroups.initiate(data, options))
  return Promise.all(store.dispatch(groupService.util.getRunningQueriesThunk()))
}

export async function createGroupAdmin(
  store: any,
  data: Req['createGroupAdmin'],
  options?: Parameters<
    typeof groupService.endpoints.createGroupAdmin.initiate
  >[1],
) {
  store.dispatch(
    groupService.endpoints.createGroupAdmin.initiate(data, options),
  )
  return Promise.all(store.dispatch(groupService.util.getRunningQueriesThunk()))
}
export async function deleteGroupAdmin(
  store: any,
  data: Req['deleteGroupAdmin'],
  options?: Parameters<
    typeof groupService.endpoints.deleteGroupAdmin.initiate
  >[1],
) {
  store.dispatch(
    groupService.endpoints.deleteGroupAdmin.initiate(data, options),
  )
  return Promise.all(store.dispatch(groupService.util.getRunningQueriesThunk()))
}
export async function deleteGroup(
  store: any,
  data: Req['deleteGroup'],
  options?: Parameters<typeof groupService.endpoints.deleteGroup.initiate>[1],
) {
  store.dispatch(groupService.endpoints.deleteGroup.initiate(data, options))
  return Promise.all(store.dispatch(groupService.util.getRunningQueriesThunk()))
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateGroupAdminMutation,
  useDeleteGroupAdminMutation,
  useDeleteGroupMutation,

  useGetGroupsQuery,
  // END OF EXPORTS
} = groupService

/* Usage examples:
const { data, isLoading } = useGetGroupsQuery({ id: 2 }, {}) //get hook
const [createGroups, { isLoading, data, isSuccess }] = useCreateGroupsMutation() //create hook
groupService.endpoints.getGroups.select({id: 2})(store.getState()) //access data from any function
*/
