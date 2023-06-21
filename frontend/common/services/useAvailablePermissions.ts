import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const availablePermissionService = service
  .enhanceEndpoints({ addTagTypes: ['AvailablePermission'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getAvailablePermissions: builder.query<
        Res['availablePermissions'],
        Req['getAvailablePermissions']
      >({
        providesTags: (res, e, query) => [
          { id: query.level, type: 'AvailablePermission' },
        ],
        query: (query: Req['getAvailablePermissions']) => ({
          url: `${query.level}s/permissions/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getAvailablePermissions(
  store: any,
  data: Req['getAvailablePermissions'],
  options?: Parameters<
    typeof availablePermissionService.endpoints.getAvailablePermissions.initiate
  >[1],
) {
  store.dispatch(
    availablePermissionService.endpoints.getAvailablePermissions.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(availablePermissionService.util.getRunningQueriesThunk()),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetAvailablePermissionsQuery,
  // END OF EXPORTS
} = availablePermissionService

/* Usage examples:
const { data, isLoading } = useGetAvailablePermissionsQuery({ id: 2 }, {}) //get hook
const [createAvailablePermissions, { isLoading, data, isSuccess }] = useCreateAvailablePermissionsMutation() //create hook
availablePermissionService.endpoints.getAvailablePermissions.select({id: 2})(store.getState()) //access data from any function
*/
