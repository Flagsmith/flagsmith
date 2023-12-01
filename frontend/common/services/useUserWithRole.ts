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
          const tags = result ? [{ type: 'User-role', id: userId }] : []
          return tags
        },
        query: (query: Req['getUserWithRoles']) => ({
          url: `organisations/${query.org_id}/user-roles/${query.user_id}/`,
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
// END OF FUNCTION_EXPORTS

export const {
  useGetUserWithRolesQuery,
  // END OF EXPORTS
} = userWithRolesService

/* Usage examples:
const { data, isLoading } = useUserWithRolesQuery({ id: 2 }, {}) //get hook
userWithRolesService.endpoints.getUserWithRoles.select({id: 2})(store.getState()) //access data from any function
*/
