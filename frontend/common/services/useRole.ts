import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const roleService = service
  .enhanceEndpoints({ addTagTypes: ['Role'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createRoles: builder.mutation<Res['roles'], Req['createRoles']>({
        invalidatesTags: [{ id: 'LIST', type: 'Role' }],
        query: (query: Req['createRoles']) => ({
          body: query,
          method: 'POST',
          url: `organisations/roles/`,
        }),
      }),
      deleteRolesById: builder.mutation<Res['roles'], Req['deleteRolesById']>({
        invalidatesTags: [{ id: 'LIST', type: 'RolesById' }],
        query: (query: Req['deleteRolesById']) => ({
          body: query,
          method: 'DELETE',
          url: `organisations/${query.organisation_id}/roles/${query.role_id}`,
        }),
      }),
      getRoles: builder.query<Res['roles'], Req['getRoles']>({
        providesTags: (res) => [{ id: res?.id, type: 'Role' }],
        query: (query: Req['getRoles']) => ({
          url: `organisations/${query.organisation_id}/roles/`,
        }),
      }),
      getRolesById: builder.query<Res['roles'], Req['getRolesById']>({
        providesTags: (res) => [{ id: res?.id, type: 'RolesById' }],
        query: (query: Req['getRolesById']) => ({
          url: `organisations/${query.organisation_id}/roles/${query.role_id}`,
        }),
      }),
      updateRolesById: builder.mutation<Res['roles'], Req['updateRolesById']>({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'RolesById' },
          { id: res?.id, type: 'RolesById' },
        ],
        query: (query: Req['updateRolesById']) => ({
          body: query,
          method: 'PUT',
          url: `organisations/${query.organisation_id}/roles/${query.role_id}`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createRoles(
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
export async function deleteRolesById(
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
export async function getRolesById(
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
export async function updateRolesById(
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
  useCreateRolesMutation,
  useDeleteRolesByIdMutation,
  useGetRolesByIdQuery,
  useGetRolesQuery,
  useUpdateRolesByIdMutation,
  // END OF EXPORTS
} = roleService

/* Usage examples:
const { data, isLoading } = useGetRolesQuery({ id: 2 }, {}) //get hook
const [createRoles, { isLoading, data, isSuccess }] = useCreateRolesMutation() //create hook
roleService.endpoints.getRoles.select({id: 2})(store.getState()) //access data from any function
*/
