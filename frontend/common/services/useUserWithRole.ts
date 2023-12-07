import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const userWithRolesService = service
  .enhanceEndpoints({ addTagTypes: ['User-role'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getUserWithRoles: builder.query<
        Res['userWithRoles'],
        Req['getUserWithRoles']
      >({
        invalidatesTags: [{ type: 'User-role' }],
        providesTags: (result, error, userId) => {
          const tags = result ? [{ id: userId, type: 'User-role' }] : []
          return tags
        },
        query: (query: Req['getUserWithRoles']) => ({
          url: `organisations/${query.org_id}/users/${query.user_id}/roles/`,
        }),
      }),
      deleteUserWithRoles: builder.mutation<Res['User-role'], Req['deleteUserWithRoles']>({
        invalidatesTags: [{ type: 'User-role' }],
        query: (query: Req['deleteUserWithRoles']) => ({
          method: 'DELETE',
          url: `organisations/${query.org_id}/users/${query.user_id}/roles/${query.role_id}/`,
        }),
        transformResponse: () => {
          toast('User role was removed')
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getUserWithRoles(
  store: any,
  data: Req['getUserWithRoles'],
  options?: Parameters<
    typeof userWithRolesService.endpoints.getUserWithRoles.initiate
  >[1],
) {
  return store.dispatch(
    userWithRolesService.endpoints.getUserWithRoles.initiate(data, options),
  )
}

export async function deleteUserRole(
  store: any,
  data: Req['deleteUserWithRoles'],
  options?: Parameters<
    typeof UserRoleService.endpoints.deleteUserWithRoles.initiate
  >[1],
) {
  return store.dispatch(
    UserRoleService.endpoints.deleteUserWithRoles.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetUserWithRolesQuery,
  useDeleteUserWithRolesMutation,
  // END OF EXPORTS
} = userWithRolesService

/* Usage examples:
const { data, isLoading } = useUserWithRolesQuery({ id: 2 }, {}) //get hook
userWithRolesService.endpoints.getUserWithRoles.select({id: 2})(store.getState()) //access data from any function
*/
