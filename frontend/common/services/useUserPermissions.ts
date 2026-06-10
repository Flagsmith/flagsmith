import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const userPermissionsService = service
  .enhanceEndpoints({ addTagTypes: ['UserPermissions'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createEnvironmentUserPermission: builder.mutation<
        Res['userPermissions'],
        Req['createEnvironmentUserPermission']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'UserPermissions' }],
        query: ({
          body,
          environmentId,
        }: Req['createEnvironmentUserPermission']) => ({
          body,
          method: 'POST',
          url: `environments/${environmentId}/user-permissions/`,
        }),
      }),
      createProjectUserPermission: builder.mutation<
        Res['userPermissions'],
        Req['createProjectUserPermission']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'UserPermissions' }],
        query: ({ body, projectId }: Req['createProjectUserPermission']) => ({
          body,
          method: 'POST',
          url: `projects/${projectId}/user-permissions/`,
        }),
      }),
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
  useCreateEnvironmentUserPermissionMutation,
  useCreateProjectUserPermissionMutation,
  useGetUserPermissionsQuery,
  // END OF EXPORTS
} = userPermissionsService

/* Usage examples:
const { data, isLoading } = useGetUserEnvironmentPermissionsQuery({ environmentId: aA1x3Ysd, userId: 1 }, {}) //get hook
userPermissionsService.endpoints.getUserEnvironmentPermissions.select({ environmentId: aA1x3Ysd, userId: 1 })(store.getState()) //access data from any function
*/
