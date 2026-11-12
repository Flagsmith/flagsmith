import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const userGroupPermissionService = service
  .enhanceEndpoints({ addTagTypes: ['UserGroupPermission'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getUserGroupPermission: builder.query<
        Res['userGroupPermissions'],
        Req['getUserGroupPermission']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'UserGroupPermission' }],
        query: (query: Req['getUserGroupPermission']) => ({
          url: `projects/${query.project_id}/user-group-permissions/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getUserGroupPermission(
  store: any,
  data: Req['getUserGroupPermission'],
  options?: Parameters<
    typeof userGroupPermissionService.endpoints.getUserGroupPermission.initiate
  >[1],
) {
  return store.dispatch(
    userGroupPermissionService.endpoints.getUserGroupPermission.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetUserGroupPermissionQuery,
  // END OF EXPORTS
} = userGroupPermissionService

/* Usage examples:
const { data, isLoading } = useGetUserGroupPermissionQuery({ id: 2 }, {}) //get hook
const [createUserGroupPermission, { isLoading, data, isSuccess }] = useCreateUserGroupPermissionMutation() //create hook
userGroupPermissionService.endpoints.getUserGroupPermission.select({id: 2})(store.getState()) //access data from any function
*/
