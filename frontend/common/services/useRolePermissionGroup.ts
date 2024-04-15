import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const rolePermissionGroupService = service
  .enhanceEndpoints({ addTagTypes: ['RolePermissionGroup', 'GroupWithRole'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createRolePermissionGroup: builder.mutation<
        Res['createRolePermissionGroup'],
        Req['createRolePermissionGroup']
      >({
        invalidatesTags: [
          { id: 'LIST', type: 'RolePermissionGroup' },
          { type: 'GroupWithRole' },
        ],
        query: (query: Req['createRolePermissionGroup']) => ({
          body: query.data,
          method: 'POST',
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/groups/`,
        }),
      }),
      deleteRolePermissionGroup: builder.mutation<
        Res['rolePermissionGroup'],
        Req['deleteRolePermissionGroup']
      >({
        invalidatesTags: [
          { type: 'RolePermissionGroup' },
          { type: 'GroupWithRole' },
        ],
        query: (query: Req['deleteRolePermissionGroup']) => ({
          body: query,
          method: 'DELETE',
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/groups/${query.group_id}/`,
        }),
      }),
      getRolePermissionGroup: builder.query<
        Res['rolePermissionGroup'],
        Req['getRolePermissionGroup']
      >({
        query: (query: Req['getRolePermissionGroup']) => ({
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/groups/`,
        }),
      }),
      updateRolePermissionGroup: builder.mutation<
        Res['rolePermissionGroup'],
        Req['updateRolePermissionGroup']
      >({
        invalidatesTags: (res) => [{ id: 'LIST', type: 'RolePermissionGroup' }],
        query: (query: Req['updateRolePermissionGroup']) => ({
          body: query,
          method: 'PUT',
          url: `organisations/${query.id}/roles/${query.role_id}/groups/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createRolePermissionGroup(
  store: any,
  data: Req['createRolePermissionGroup'],
  options?: Parameters<
    typeof rolePermissionGroupService.endpoints.createRolePermissionGroup.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionGroupService.endpoints.createRolePermissionGroup.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(rolePermissionGroupService.util.getRunningQueriesThunk()),
  )
}
export async function deleteRolePermissionGroup(
  store: any,
  data: Req['deleteRolePermissionGroup'],
  options?: Parameters<
    typeof rolePermissionGroupService.endpoints.deleteRolePermissionGroup.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionGroupService.endpoints.deleteRolePermissionGroup.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(rolePermissionGroupService.util.getRunningQueriesThunk()),
  )
}
export async function getRolePermissionGroup(
  store: any,
  data: Req['getRolePermissionGroup'],
  options?: Parameters<
    typeof rolePermissionGroupService.endpoints.getRolePermissionGroup.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionGroupService.endpoints.getRolePermissionGroup.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(rolePermissionGroupService.util.getRunningQueriesThunk()),
  )
}
export async function updateRolePermissionGroup(
  store: any,
  data: Req['updateRolePermissionGroup'],
  options?: Parameters<
    typeof rolePermissionGroupService.endpoints.updateRolePermissionGroup.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionGroupService.endpoints.updateRolePermissionGroup.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(rolePermissionGroupService.util.getRunningQueriesThunk()),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateRolePermissionGroupMutation,
  useDeleteRolePermissionGroupMutation,
  useGetRolePermissionGroupQuery,
  useUpdateRolePermissionGroupMutation,
  // END OF EXPORTS
} = rolePermissionGroupService

/* Usage examples:
const { data, isLoading } = useGetRolePermissionGroupQuery({ id: 2 }, {}) //get hook
const [createRolePermissionGroup, { isLoading, data, isSuccess }] = useCreateRolePermissionGroupMutation() //create hook
rolePermissionGroupService.endpoints.getRolePermissionGroup.select({id: 2})(store.getState()) //access data from any function
*/
