import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const rolePermissionService = service
  .enhanceEndpoints({ addTagTypes: ['RolePermission'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createRoleEnvironmentPermissions: builder.mutation<
        Res['rolePermission'],
        Req['createRolePermission']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'RolePermission' },
          { id: res?.id, type: 'RolePermission' },
        ],
        query: (query: Req['updateRolePermission']) => ({
          body: query.body,
          method: 'POST',
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/environments-permissions/`,
        }),
      }),
      createRoleOrganisationPermissions: builder.mutation<
        Res['rolePermission'],
        Req['createRolePermission']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'RolePermission' },
          { id: res?.id, type: 'RolePermission' },
        ],
        query: (query: Req['updateRolePermission']) => ({
          body: query,
          method: 'POST',
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/organisation-permissions/`,
        }),
      }),

      createRoleProjectPermissions: builder.mutation<
        Res['rolePermission'],
        Req['createRolePermission']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'RolePermission' },
          { id: res?.id, type: 'RolePermission' },
        ],
        query: (query: Req['updateRolePermission']) => ({
          body: query.body,
          method: 'POST',
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/projects-permissions/`,
        }),
      }),
      getRoleEnvironmentPermissions: builder.query<
        Res['rolePermission'],
        Req['getRolePermission']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'RolePermission' }],
        query: (query: Req['getRolePermission']) => ({
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/environments-permissions/?environment=${query.env_id}`,
        }),
      }),
      getRoleOrganisationPermissions: builder.query<
        Res['rolePermission'],
        Req['getRolePermission']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'RolePermission' }],
        query: (query: Req['getRolePermission']) => ({
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/organisation-permissions/`,
        }),
      }),
      getRoleProjectPermissions: builder.query<
        Res['rolePermission'],
        Req['getRolePermission']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'RolePermission' }],
        query: (query: Req['getRolePermission']) => ({
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/projects-permissions/?project=${query.project_id}`,
        }),
      }),

      getRolesEnvironmentPermissions: builder.query<
        Res['rolePermission'],
        Req['getRolePermission']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'RolePermission' }],
        query: (query: Req['getRolePermission']) => ({
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/environments-permissions/?environment=${query.env_id}`,
        }),
      }),

      getRolesProjectPermissions: builder.query<
        Res['rolePermission'],
        Req['getRolePermission']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'RolePermission' }],
        query: (query: Req['getRolePermission']) => ({
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/projects-permissions/?project=${query.project_id}`,
        }),
      }),

      updateRoleEnvironmentPermissions: builder.mutation<
        Res['rolePermission'],
        Req['updateRolePermission']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'RolePermission' },
          { id: res?.id, type: 'RolePermission' },
        ],
        query: (query: Req['updateRolePermission']) => ({
          body: query.body,
          method: 'PUT',
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/environments-permissions/${query.id}/`,
        }),
      }),

      updateRoleOrganisationPermissions: builder.mutation<
        Res['rolePermission'],
        Req['updateRolePermission']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'RolePermission' },
          { id: res?.id, type: 'RolePermission' },
        ],
        query: (query: Req['updateRolePermission']) => ({
          body: query.body,
          method: 'PUT',
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/organisation-permissions/${query.id}/`,
        }),
      }),

      updateRoleProjectPermissions: builder.mutation<
        Res['rolePermission'],
        Req['updateRolePermission']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'RolePermission' },
          { id: res?.id, type: 'RolePermission' },
        ],
        query: (query: Req['updateRolePermission']) => ({
          body: query.body,
          method: 'PUT',
          url: `organisations/${query.organisation_id}/roles/${query.role_id}/projects-permissions/${query.id}/`,
        }),
      }),

      // END OF ENDPOINTS
    }),
  })

export async function getRoleOrganisationPermissions(
  store: any,
  data: Req['getRolePermission'],
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
export async function updateRoleOrganisationPermissions(
  store: any,
  data: Req['updateRolePermission'],
  options?: Parameters<
    typeof rolePermissionService.endpoints.updateRoleOrganisationPermissions.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionService.endpoints.updateRoleOrganisationPermissions.initiate(
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
  data: Req['getRolePermission'],
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
export async function getRolesProjectPermissions(
  store: any,
  data: Req['getRolesPermission'],
  options?: Parameters<
    typeof rolePermissionService.endpoints.getRolesProjectPermissions.initiate
  >[1],
) {
  return store.dispatch(
    rolePermissionService.endpoints.getRolesProjectPermissions.initiate(
      data,
      options,
    ),
  )
}

export async function updateRoleProjectPermissions(
  store: any,
  data: Req['updateRolePermission'],
  options?: Parameters<
    typeof rolePermissionService.endpoints.updateRoleProjectPermissions.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionService.endpoints.updateRoleProjectPermissions.initiate(
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
  data: Req['getRolePermission'],
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

export async function getRolesEnvironmentPermissions(
  store: any,
  data: Req['getRolesEnvironment'],
  options?: Parameters<
    typeof rolePermissionService.endpoints.getRolesProjectPermissions.initiate
  >[1],
) {
  return store.dispatch(
    rolePermissionService.endpoints.getRolesEnvironmentPermissions.initiate(
      data,
      options,
    ),
  )
}
export async function updateRoleEnvironmentPermissions(
  store: any,
  data: Req['updateRolePermission'],
  options?: Parameters<
    typeof rolePermissionService.endpoints.updateRoleEnvironmentPermissions.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionService.endpoints.updateRoleEnvironmentPermissions.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(rolePermissionService.util.getRunningQueriesThunk()),
  )
}

export async function createRoleOrganisationPermissions(
  store: any,
  data: Req['updateRolePermission'],
  options?: Parameters<
    typeof rolePermissionService.endpoints.createRoleOrganisationPermissions.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionService.endpoints.createRoleOrganisationPermissions.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(rolePermissionService.util.getRunningQueriesThunk()),
  )
}

export async function createRoleProjectPermissions(
  store: any,
  data: Req['updateRolePermission'],
  options?: Parameters<
    typeof rolePermissionService.endpoints.createRoleProjectPermissions.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionService.endpoints.createRoleProjectPermissions.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(rolePermissionService.util.getRunningQueriesThunk()),
  )
}

export async function createRoleEnvironmentPermissions(
  store: any,
  data: Req['updateRolePermission'],
  options?: Parameters<
    typeof rolePermissionService.endpoints.createRoleEnvironmentPermissions.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionService.endpoints.createRoleEnvironmentPermissions.initiate(
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
  useCreateRoleEnvironmentPermissionsMutation,
  useCreateRoleOrganisationPermissionsMutation,
  useCreateRoleProjectPermissionsMutation,
  useGetRoleEnvironmentPermissionsQuery,
  useGetRoleOrganisationPermissionsQuery,
  useGetRoleProjectPermissionsQuery,
  useUpdateRoleEnvironmentPermissionsMutation,
  useUpdateRoleOrganisationPermissionsMutation,
  useUpdateRoleProjectPermissionsMutation,
  // END OF EXPORTS
} = rolePermissionService

/* Usage examples:
const { data, isLoading } = useGetRoleOrganisationPermissionsQuery({ id: 2 }, {}) //get hook
const [createRolePermission, { isLoading, data, isSuccess }] = useCreateRolePermissionMutation() //create hook
rolePermissionService.endpoints.getRolePermission.select({id: 2})(store.getState()) //access data from any function
*/
