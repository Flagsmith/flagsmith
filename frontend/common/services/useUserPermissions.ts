import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const userPermissionsService = service
  .enhanceEndpoints({ addTagTypes: ['UserPermissions'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getUserPermissions: builder.query<
        Res['userPermissions'],
        Req['getUserPermissions']
      >({
        providesTags: [{ id: 'LIST', type: 'UserPermissions' }],
        query: (query: Req['getUserPermissions']) => ({
          url: `${query.level}s/${query.id}/user-detailed-permissions/${query.userId}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getUserPermissions(
  store: any,
  data: Req['getUserPermissions'],
  options?: Parameters<
    typeof userPermissionsService.endpoints.getUserPermissions.initiate
  >[1],
) {
  return store.dispatch(
    userPermissionsService.endpoints.getUserPermissions.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetUserPermissionsQuery,
  // END OF EXPORTS
} = userPermissionsService

/* Usage examples:
const { data, isLoading } = useGetUserEnvironmentPermissionsQuery({ environmentId: aA1x3Ysd, userId: 1 }, {}) //get hook
userPermissionsService.endpoints.getUserEnvironmentPermissions.select({ environmentId: aA1x3Ysd, userId: 1 })(store.getState()) //access data from any function
*/
