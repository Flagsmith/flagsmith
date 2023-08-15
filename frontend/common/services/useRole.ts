import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const roleService = service
  .enhanceEndpoints({ addTagTypes: ['Role'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createRole: builder.mutation<Res['roles'], Req['createRoles']>({
        invalidatesTags: [{ id: 'LIST', type: 'Role' }],
        query: (query: Req['createRoles']) => ({
          body: query,
          method: 'POST',
          url: `organisations/${query.organisation_id}/roles/`,
        }),
      }),
      deleteRole: builder.mutation<Res['roles'], Req['deleteRolesById']>({
        invalidatesTags: [{ id: 'LIST', type: 'DeleteRole' }],
        query: (query: Req['deleteRole']) => ({
          method: 'DELETE',
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/`,
        }),
      }),
      getRoles: builder.query<Res['roles'], Req['getRoles']>({
        providesTags: (res) => [{ id: res?.id, type: 'Role' }],
        query: (query: Req['getRoles']) => ({
          url: `organisations/${query.organisation_id}/roles/`,
        }),
      }),
      getRole: builder.query<Res['roles'], Req['getRolesById']>({
        providesTags: (res) => [{ id: res?.id, type: 'RolesById' }],
        query: (query: Req['getRolesById']) => ({
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/`,
        }),
      }),
      updateRole: builder.mutation<Res['roles'], Req['updateRolesById']>({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'RolesById' },
          { id: res?.id, type: 'RolesById' },
        ],
        query: (query: Req['updateRole']) => ({
          body: query.body,
          method: 'PUT',
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createRole(
  store: any,
  data: Req['createRoles'],
  options?: Parameters<typeof roleService.endpoints.createRoles.initiate>[1],
) {
  store.dispatch(roleService.endpoints.createRoles.initiate(data, options))
  return Promise.all(store.dispatch(roleService.util.getRunningQueriesThunk()))
}
export async function getRoles(
  store: any,
  data: Req['getRoles'],
  options?: Parameters<typeof roleService.endpoints.getRoles.initiate>[1],
) {
  store.dispatch(roleService.endpoints.getRoles.initiate(data, options))
  return Promise.all(store.dispatch(roleService.util.getRunningQueriesThunk()))
}
export async function deleteRole(
  store: any,
  data: Req['deleteRolesById'],
  options?: Parameters<
    typeof rolesByIdService.endpoints.deleteRolesById.initiate
  >[1],
) {
  store.dispatch(
    rolesByIdService.endpoints.deleteRolesById.initiate(data, options),
  )
  return Promise.all(
    store.dispatch(rolesByIdService.util.getRunningQueriesThunk()),
  )
}
export async function getRole(
  store: any,
  data: Req['getRolesById'],
  options?: Parameters<
    typeof rolesByIdService.endpoints.getRolesById.initiate
  >[1],
) {
  store.dispatch(
    rolesByIdService.endpoints.getRolesById.initiate(data, options),
  )
  return Promise.all(
    store.dispatch(rolesByIdService.util.getRunningQueriesThunk()),
  )
}
export async function updateRole(
  store: any,
  data: Req['updateRolesById'],
  options?: Parameters<
    typeof rolesByIdService.endpoints.updateRolesById.initiate
  >[1],
) {
  store.dispatch(
    rolesByIdService.endpoints.updateRolesById.initiate(data, options),
  )
  return Promise.all(
    store.dispatch(rolesByIdService.util.getRunningQueriesThunk()),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateRoleMutation,
  useDeleteRoleMutation,
  useGetRoleQuery,
  useGetRolesQuery,
  useUpdateRoleMutation,
  // END OF EXPORTS
} = roleService

/* Usage examples:
const { data, isLoading } = useGetRolesQuery({ id: 2 }, {}) //get hook
const [createRole, { isLoading, data, isSuccess }] = useCreateRoleMutation() //create hook
roleService.endpoints.getRoles.select({id: 2})(store.getState()) //access data from any function
*/
