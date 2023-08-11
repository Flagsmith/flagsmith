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
      deleteRoles: builder.mutation<Res['roles'], Req['deleteRoles']>({
        invalidatesTags: [{ id: 'LIST', type: 'Role' }],
        query: (query: Req['deleteRoles']) => ({
          body: query,
          method: 'DELETE',
          url: `organisations/${query.id}/roles/`,
        }),
      }),
      getRoles: builder.query<Res['roles'], Req['getRoles']>({
        providesTags: (res) => [{ id: res?.id, type: 'Role' }],
        query: (query: Req['getRoles']) => ({
          url: `organisations/${query.id}/roles/`,
        }),
      }),
      updateRoles: builder.mutation<Res['roles'], Req['updateRoles']>({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'Role' },
          { id: res?.id, type: 'Role' },
        ],
        query: (query: Req['updateRoles']) => ({
          body: query,
          method: 'PUT',
          url: `organisations/${query.id}/roles/`,
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
export async function deleteRoles(
  store: any,
  data: Req['deleteRoles'],
  options?: Parameters<typeof roleService.endpoints.deleteRoles.initiate>[1],
) {
  store.dispatch(roleService.endpoints.deleteRoles.initiate(data, options))
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
export async function updateRoles(
  store: any,
  data: Req['updateRoles'],
  options?: Parameters<typeof roleService.endpoints.updateRoles.initiate>[1],
) {
  store.dispatch(roleService.endpoints.updateRoles.initiate(data, options))
  return Promise.all(store.dispatch(roleService.util.getRunningQueriesThunk()))
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateRolesMutation,
  useDeleteRolesMutation,
  useGetRolesQuery,
  useUpdateRolesMutation,
  // END OF EXPORTS
} = roleService

/* Usage examples:
const { data, isLoading } = useGetRolesQuery({ id: 2 }, {}) //get hook
const [createRoles, { isLoading, data, isSuccess }] = useCreateRolesMutation() //create hook
roleService.endpoints.getRoles.select({id: 2})(store.getState()) //access data from any function
*/
