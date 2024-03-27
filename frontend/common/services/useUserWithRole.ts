import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const userWithRolesService = service
  .enhanceEndpoints({ addTagTypes: ['RolesUser'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      deleteUserWithRoles: builder.mutation<{}, Req['deleteUserWithRole']>({
        invalidatesTags: [{ type: 'RolesUser' }],
        query: (query: Req['deleteUserWithRole']) => ({
          method: 'DELETE',
          url: `organisations/${query.org_id}/users/${query.user_id}/roles/${query.role_id}/`,
        }),
      }),
      getUserWithRoles: builder.query<
        Res['userWithRoles'],
        Req['getUserWithRoles']
      >({
        providesTags: (result, error, req) => {
          return result
            ? [{ id: `${req.user_id}-${req.org_id}`, type: 'RolesUser' }]
            : []
        },
        query: (query: Req['getUserWithRoles']) => ({
          url: `organisations/${query.org_id}/users/${query.user_id}/roles/`,
        }),
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
  data: Req['deleteUserWithRole'],
  options?: Parameters<
    typeof userWithRolesService.endpoints.deleteUserWithRoles.initiate
  >[1],
) {
  return store.dispatch(
    userWithRolesService.endpoints.deleteUserWithRoles.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useDeleteUserWithRolesMutation,
  useGetUserWithRolesQuery,
  // END OF EXPORTS
} = userWithRolesService

/* Usage examples:
const { data, isLoading } = useUserWithRolesQuery({ id: 2 }, {}) //get hook
userWithRolesService.endpoints.getUserWithRoles.select({id: 2})(store.getState()) //access data from any function
*/
