import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const groupWithRoleService = service
  .enhanceEndpoints({ addTagTypes: ['GroupWithRole', 'RolePermissionGroup'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      deleteGroupWithRole: builder.mutation<
        Res['groupWithRole'],
        Req['deleteGroupWithRole']
      >({
        invalidatesTags: [
          { type: 'GroupWithRole' },
          { type: 'RolePermissionGroup' },
        ],
        query: (query: Req['deleteGroupWithRole']) => ({
          body: query,
          method: 'DELETE',
          url: `organisations/${query.org_id}/groups/${query.group_id}/roles/${query.role_id}/`,
        }),
      }),
      getGroupWithRole: builder.query<
        Res['groupWithRole'],
        Req['getGroupWithRole']
      >({
        providesTags: (result, error, group) => {
          const tags = result ? [{ id: group.id, type: 'GroupWithRole' }] : []
          return tags
        },
        query: (query: Req['getGroupWithRole']) => ({
          url: `organisations/${query.org_id}/groups/${query.group_id}/roles/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function deleteGroupWithRole(
  store: any,
  data: Req['deleteGroupWithRole'],
  options?: Parameters<
    typeof groupWithRoleService.endpoints.deleteGroupWithRole.initiate
  >[1],
) {
  return store.dispatch(
    groupWithRoleService.endpoints.deleteGroupWithRole.initiate(data, options),
  )
}
export async function getGroupWithRole(
  store: any,
  data: Req['getGroupWithRole'],
  options?: Parameters<
    typeof groupWithRoleService.endpoints.getGroupWithRole.initiate
  >[1],
) {
  return store.dispatch(
    groupWithRoleService.endpoints.getGroupWithRole.initiate(data, options),
  )
}

// END OF FUNCTION_EXPORTS

export const {
  useDeleteGroupWithRoleMutation,
  useGetGroupWithRoleQuery,
  // END OF EXPORTS
} = groupWithRoleService

/* Usage examples:
const { data, isLoading } = useGetGroupWithRoleQuery({ id: 2 }, {}) //get hook
const [createGroupWithRole, { isLoading, data, isSuccess }] = useCreateGroupWithRoleMutation() //create hook
groupWithRoleService.endpoints.getGroupWithRole.select({id: 2})(store.getState()) //access data from any function
*/
