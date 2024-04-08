import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const roleService = service
  .enhanceEndpoints({ addTagTypes: ['Role'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createRole: builder.mutation<Res['role'], Req['createRole']>({
        invalidatesTags: [{ id: 'LIST', type: 'Role' }],
        query: (query: Req['createRole']) => ({
          body: query,
          method: 'POST',
          url: `organisations/${query.organisation_id}/roles/`,
        }),
      }),
      deleteRole: builder.mutation<Res['role'], Req['deleteRole']>({
        invalidatesTags: [{ id: 'LIST', type: 'Role' }],
        query: (query: Req['deleteRole']) => ({
          method: 'DELETE',
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/`,
        }),
      }),
      getRole: builder.query<Res['role'], Req['getRole']>({
        query: (query: Req['getRole']) => ({
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/`,
        }),
      }),
      getRoles: builder.query<Res['roles'], Req['getRoles']>({
        providesTags: [{ id: 'LIST', type: 'Role' }],
        query: (query: Req['getRoles']) => ({
          url: `organisations/${query.organisation_id}/roles/`,
        }),
      }),
      updateRole: builder.mutation<Res['roles'], Req['updateRole']>({
        invalidatesTags: (res) => [{ id: 'LIST', type: 'Role' }],
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
  data: Req['createRole'],
  options?: Parameters<typeof roleService.endpoints.createRole.initiate>[1],
) {
  store.dispatch(roleService.endpoints.createRole.initiate(data, options))
  return Promise.all(store.dispatch(roleService.util.getRunningQueriesThunk()))
}
export async function getRoles(
  store: any,
  data: Req['getRoles'],
  options?: Parameters<typeof roleService.endpoints.getRoles.initiate>[1],
) {
  return store.dispatch(roleService.endpoints.getRoles.initiate(data, options))
}
export async function deleteRole(
  store: any,
  data: Req['deleteRole'],
  options?: Parameters<typeof roleService.endpoints.deleteRole.initiate>[1],
) {
  store.dispatch(roleService.endpoints.deleteRole.initiate(data, options))
  return Promise.all(store.dispatch(roleService.util.getRunningQueriesThunk()))
}
export async function getRole(
  store: any,
  data: Req['getRole'],
  options?: Parameters<typeof roleService.endpoints.getRole.initiate>[1],
) {
  store.dispatch(roleService.endpoints.getRole.initiate(data, options))
  return Promise.all(store.dispatch(roleService.util.getRunningQueriesThunk()))
}
export async function updateRole(
  store: any,
  data: Req['updateRole'],
  options?: Parameters<typeof roleService.endpoints.updateRole.initiate>[1],
) {
  store.dispatch(roleService.endpoints.updateRole.initiate(data, options))
  return Promise.all(store.dispatch(roleService.util.getRunningQueriesThunk()))
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
