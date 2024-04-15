import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const rolePermissionService = service
  .enhanceEndpoints({ addTagTypes: ['rolePermission'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createRolePermissions: builder.mutation<
        Res['rolePermission'],
        Req['createRolePermission']
      >({
        invalidatesTags: (res, req) => [{ type: 'rolePermission' }],
        query: (query: Req['updateRolePermission']) => ({
          body: query.body,
          method: 'POST',
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/${query.level}-permissions/`,
        }),
      }),

      getRoleEnvironmentPermissions: builder.query<
        Res['rolePermission'],
        Req['getRolePermissionEnvironment']
      >({
        providesTags: (res, _, req) => [
          {
            id: `LIST-${req.organisation_id}-${req.role_id}-${req.env_id}`,
            type: 'rolePermission',
          },
        ],
        query: (query: Req['getRolePermissionEnvironment']) => ({
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/environments-permissions/?environment=${query.env_id}`,
        }),
      }),

      getRoleOrganisationPermissions: builder.query<
        Res['rolePermission'],
        Req['getRolePermissionOrganisation']
      >({
        providesTags: (res, _, req) => [
          {
            id: `LIST-${req.organisation_id}-${req.role_id}`,
            type: 'rolePermission',
          },
        ],
        query: (query: Req['getRolePermissionOrganisation']) => ({
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/organisation-permissions/`,
        }),
      }),

      getRoleProjectPermissions: builder.query<
        Res['rolePermission'],
        Req['getRolePermissionProject']
      >({
        providesTags: (res, _, req) => [
          {
            id: `LIST-${req.organisation_id}-${req.role_id}-${req.project_id}`,
            type: 'rolePermission',
          },
        ],
        query: (query: Req['getRolePermissionProject']) => ({
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/projects-permissions/?project=${query.project_id}`,
        }),
      }),

      updateRolePermissions: builder.mutation<
        Res['rolePermission'],
        Req['updateRolePermission']
      >({
        invalidatesTags: [{ type: 'rolePermission' }],
        query: (query: Req['updateRolePermission']) => ({
          body: query.body,
          method: 'PUT',
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/${query.level}-permissions/${query.id}/`,
        }),
      }),

      // END OF ENDPOINTS
    }),
  })

export async function getRoleOrganisationPermissions(
  store: any,
  data: Req['getRolePermissionOrganisation'],
  options?: Parameters<
    typeof rolePermissionService.endpoints.getRoleOrganisationPermissions.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionService.endpoints.getRoleOrganisationPermissions.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(rolePermissionService.util.getRunningQueriesThunk()),
  )
}
export async function updateRolePermissions(
  store: any,
  data: Req['updateRolePermission'],
  options?: Parameters<
    typeof rolePermissionService.endpoints.updateRolePermissions.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionService.endpoints.updateRolePermissions.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(rolePermissionService.util.getRunningQueriesThunk()),
  )
}

export async function getRoleProjectPermissions(
  store: any,
  data: Req['getRolePermissionProject'],
  options?: Parameters<
    typeof rolePermissionService.endpoints.getRoleProjectPermissions.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionService.endpoints.getRoleProjectPermissions.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(rolePermissionService.util.getRunningQueriesThunk()),
  )
}

export async function getRoleEnvironmentPermissions(
  store: any,
  data: Req['getRolePermissionEnvironment'],
  options?: Parameters<
    typeof rolePermissionService.endpoints.getRoleEnvironmentPermissions.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionService.endpoints.getRoleEnvironmentPermissions.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(rolePermissionService.util.getRunningQueriesThunk()),
  )
}

export async function createRolePermissions(
  store: any,
  data: Req['updateRolePermission'],
  options?: Parameters<
    typeof rolePermissionService.endpoints.createRolePermissions.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionService.endpoints.createRolePermissions.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(rolePermissionService.util.getRunningQueriesThunk()),
  )
}

// END OF FUNCTION_EXPORTS

export const {
  useCreateRolePermissionsMutation,
  useGetRoleEnvironmentPermissionsQuery,
  useGetRoleOrganisationPermissionsQuery,
  useGetRoleProjectPermissionsQuery,
  useUpdateRolePermissionsMutation,
  // END OF EXPORTS
} = rolePermissionService

/* Usage examples:
const { data, isLoading } = useGetRoleOrganisationPermissionsQuery({ id: 2 }, {}) //get hook
const [createRolePermission, { isLoading, data, isSuccess }] = useCreateRolePermissionMutation() //create hook
rolePermissionService.endpoints.getRolePermission.select({id: 2})(store.getState()) //access data from any function
*/
