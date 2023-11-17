import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const rolesUserService = service
  .enhanceEndpoints({ addTagTypes: ['RolesUser'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createRolesPermissionUsers: builder.mutation<
        Res['rolesUsers'],
        Req['createRolesPermissionUsers']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'RolesUser' }],
        query: (query: Req['createRolesPermissionUsers']) => ({
          body: query.data,
          method: 'POST',
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/users/`,
        }),
      }),
      deleteRolesPermissionUsers: builder.mutation<
        Res['rolesUsers'],
        Req['deleteRolesPermissionUsers']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'RolesUser' }],
        query: (query: Req['deleteRolesPermissionUsers']) => ({
          body: query,
          method: 'DELETE',
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/users/${query.user_id}/`,
        }),
      }),
      getRolesPermissionUsers: builder.query<
        Res['rolesUsers'],
        Req['getRolesPermissionUsers']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'RolesUser' }],
        query: (query: Req['getRolesPermissionUsers']) => ({
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/users/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createPermissionRolesUsers(
  store: any,
  data: Req['createRolesUsers'],
  options?: Parameters<
    typeof rolesUserService.endpoints.createRolesUsers.initiate
  >[1],
) {
  return store.dispatch(
    rolesUserService.endpoints.createRolesUsers.initiate(data, options),
  )
}
export async function deletePermissionRolesUsers(
  store: any,
  data: Req['deleteRolesPermissionUsers'],
  options?: Parameters<
    typeof rolesUserService.endpoints.deleteRolesUsers.initiate
  >[1],
) {
  return store.dispatch(
    rolesUserService.endpoints.deleteRolesUsers.initiate(data, options),
  )
}
export async function getRolesPermissionUsers(
  store: any,
  data: Req['getRolesPermissionUsers'],
  options?: Parameters<
    typeof rolesUserService.endpoints.getRolesUsers.initiate
  >[1],
) {
  return store.dispatch(
    rolesUserService.endpoints.getRolesUsers.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateRolesPermissionUsersMutation,
  useDeleteRolesPermissionUsersMutation,
  useGetRolesPermissionUsersQuery,
  // END OF EXPORTS
} = rolesUserService

/* Usage examples:
const { data, isLoading } = useGetRolesPermissionUsersQuery({ id: 2 }, {}) //get hook
const [createRolesUsers, { isLoading, data, isSuccess }] = useCreateRolesPermissionUsersMutation() //create hook
rolesUserService.endpoints.getRolesPermissionUsers.select({id: 2})(store.getState()) //access data from any function
*/
