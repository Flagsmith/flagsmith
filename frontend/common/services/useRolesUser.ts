import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const rolesUserService = service
  .enhanceEndpoints({ addTagTypes: ['RolesUser'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createRolesPermissionUsers: builder.mutation<
        Res['createRolesPermissionUsers'],
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
        Res['rolesPermissionUsers'],
        Req['deleteRolesPermissionUsers']
      >({
        invalidatesTags: [{ type: 'RolesUser' }],
        query: (query: Req['deleteRolesPermissionUsers']) => ({
          body: query,
          method: 'DELETE',
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/users/${query.user_id}/`,
        }),
      }),
      getRolesPermissionUsers: builder.query<
        Res['rolesPermissionUsers'],
        Req['getRolesPermissionUsers']
      >({
        query: (query: Req['getRolesPermissionUsers']) => ({
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/users/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createPermissionRolesUsers(
  store: any,
  data: Req['createRolesPermissionUsers'],
  options?: Parameters<
    typeof rolesUserService.endpoints.createRolesPermissionUsers.initiate
  >[1],
) {
  return store.dispatch(
    rolesUserService.endpoints.createRolesPermissionUsers.initiate(
      data,
      options,
    ),
  )
}
export async function deletePermissionRolesUsers(
  store: any,
  data: Req['deleteRolesPermissionUsers'],
  options?: Parameters<
    typeof rolesUserService.endpoints.deleteRolesPermissionUsers.initiate
  >[1],
) {
  return store.dispatch(
    rolesUserService.endpoints.deleteRolesPermissionUsers.initiate(
      data,
      options,
    ),
  )
}

export async function getRolesPermissionUsers(
  store: any,
  data: Req['getRolesPermissionUsers'],
  options?: Parameters<
    typeof rolesUserService.endpoints.getRolesPermissionUsers.initiate
  >[1],
) {
  return store.dispatch(
    rolesUserService.endpoints.getRolesPermissionUsers.initiate(data, options),
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
