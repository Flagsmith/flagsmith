import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const rolePermissionService = service
  .enhanceEndpoints({ addTagTypes: ['RolePermission'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createRoleEnvironmentPermission: builder.mutation<
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
      createRoleOrganisationPermission: builder.mutation<
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

      createRoleProjectPermission: builder.mutation<
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

      updateRoleEnvironmentPermission: builder.mutation<
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

      updateRoleOrganisationPermission: builder.mutation<
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

      updateRoleProjectPermission: builder.mutation<
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
export async function updateRoleOrganisationPermission(
  store: any,
  data: Req['updateRolePermission'],
  options?: Parameters<
    typeof rolePermissionService.endpoints.updateRoleOrganisationPermission.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionService.endpoints.updateRoleOrganisationPermission.initiate(
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
export async function updateRoleProjectPermission(
  store: any,
  data: Req['updateRolePermission'],
  options?: Parameters<
    typeof rolePermissionService.endpoints.updateRoleProjectPermission.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionService.endpoints.updateRoleProjectPermission.initiate(
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
export async function updateRoleEnvironmentPermission(
  store: any,
  data: Req['updateRolePermission'],
  options?: Parameters<
    typeof rolePermissionService.endpoints.updateRoleEnvironmentPermission.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionService.endpoints.updateRoleEnvironmentPermission.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(rolePermissionService.util.getRunningQueriesThunk()),
  )
}

export async function createRoleOrganisationPermission(
  store: any,
  data: Req['updateRolePermission'],
  options?: Parameters<
    typeof rolePermissionService.endpoints.createRoleOrganisationPermission.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionService.endpoints.createRoleOrganisationPermission.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(rolePermissionService.util.getRunningQueriesThunk()),
  )
}

export async function createRoleProjectPermission(
  store: any,
  data: Req['updateRolePermission'],
  options?: Parameters<
    typeof rolePermissionService.endpoints.createRoleProjectPermission.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionService.endpoints.createRoleProjectPermission.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(rolePermissionService.util.getRunningQueriesThunk()),
  )
}

export async function createRoleEnvironmentPermission(
  store: any,
  data: Req['updateRolePermission'],
  options?: Parameters<
    typeof rolePermissionService.endpoints.createRoleEnvironmentPermission.initiate
  >[1],
) {
  store.dispatch(
    rolePermissionService.endpoints.createRoleEnvironmentPermission.initiate(
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
  useCreateRoleEnvironmentPermissionMutation,
  useCreateRoleOrganisationPermissionMutation,
  useCreateRoleProjectPermissionMutation,
  useGetRoleEnvironmentPermissionsQuery,
  useGetRoleOrganisationPermissionsQuery,
  useGetRoleProjectPermissionsQuery,
  useUpdateRoleEnvironmentPermissionMutation,
  useUpdateRoleOrganisationPermissionMutation,
  useUpdateRoleProjectPermissionMutation,
  // END OF EXPORTS
} = rolePermissionService

/* Usage examples:
const { data, isLoading } = useGetRoleOrganisationPermissionsQuery({ id: 2 }, {}) //get hook
const [createRolePermission, { isLoading, data, isSuccess }] = useCreateRolePermissionMutation() //create hook
rolePermissionService.endpoints.getRolePermission.select({id: 2})(store.getState()) //access data from any function
*/
