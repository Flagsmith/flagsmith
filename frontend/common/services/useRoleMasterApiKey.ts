import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const roleMasterApiKeyService = service
  .enhanceEndpoints({
    addTagTypes: ['RoleMasterApiKey', 'MasterAPIKeyWithMasterAPIKeyRole'],
  })
  .injectEndpoints({
    endpoints: (builder) => ({
      createRoleMasterApiKey: builder.mutation<
        Res['roleMasterApiKey'],
        Req['createRoleMasterApiKey']
      >({
        invalidatesTags: [
          { id: 'LIST', type: 'RoleMasterApiKey' },
          'MasterAPIKeyWithMasterAPIKeyRole',
        ],
        query: (query: Req['createRoleMasterApiKey']) => ({
          body: query.body,
          method: 'POST',
          url: `organisations/${query.org_id}/roles/${query.role_id}/master-api-keys/`,
        }),
      }),
      deleteRoleMasterApiKey: builder.mutation<
        Res['roleMasterApiKey'],
        Req['deleteRoleMasterApiKey']
      >({
        invalidatesTags: [
          { id: 'LIST', type: 'RoleMasterApiKey' },
          'MasterAPIKeyWithMasterAPIKeyRole',
        ],
        query: (query: Req['deleteRoleMasterApiKey']) => ({
          method: 'DELETE',
          url: `organisations/${query.org_id}/roles/${query.role_id}/master-api-keys/${query.id}/`,
        }),
      }),
      getRoleMasterApiKey: builder.query<
        Res['roleMasterApiKey'],
        Req['getRoleMasterApiKey']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'RoleMasterApiKey' }],
        query: (query: Req['getRoleMasterApiKey']) => ({
          url: `organisations/${query.org_id}/roles/${query.role_id}/master-api-keys/${query.prefix}/`,
        }),
      }),
      updateRoleMasterApiKey: builder.mutation<
        Res['roleMasterApiKey'],
        Req['updateRoleMasterApiKey']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'RoleMasterApiKey' },
          { id: res?.id, type: 'RoleMasterApiKey' },
        ],
        query: (query: Req['updateRoleMasterApiKey']) => ({
          body: query,
          method: 'PUT',
          url: `organisations/${query.org_id}/roles/${query.role_id}/master-api-keys/${id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createRoleMasterApiKey(
  store: any,
  data: Req['createRoleMasterApiKey'],
  options?: Parameters<
    typeof roleMasterApiKeyService.endpoints.createRoleMasterApiKey.initiate
  >[1],
) {
  return store.dispatch(
    roleMasterApiKeyService.endpoints.createRoleMasterApiKey.initiate(
      data,
      options,
    ),
  )
}
export async function deleteRoleMasterApiKey(
  store: any,
  data: Req['deleteRoleMasterApiKey'],
  options?: Parameters<
    typeof roleMasterApiKeyService.endpoints.deleteRoleMasterApiKey.initiate
  >[1],
) {
  return store.dispatch(
    roleMasterApiKeyService.endpoints.deleteRoleMasterApiKey.initiate(
      data,
      options,
    ),
  )
}
export async function getRoleMasterApiKey(
  store: any,
  data: Req['getRoleMasterApiKey'],
  options?: Parameters<
    typeof roleMasterApiKeyService.endpoints.getRoleMasterApiKey.initiate
  >[1],
) {
  return store.dispatch(
    roleMasterApiKeyService.endpoints.getRoleMasterApiKey.initiate(
      data,
      options,
    ),
  )
}
export async function updateRoleMasterApiKey(
  store: any,
  data: Req['updateRoleMasterApiKey'],
  options?: Parameters<
    typeof roleMasterApiKeyService.endpoints.updateRoleMasterApiKey.initiate
  >[1],
) {
  return store.dispatch(
    roleMasterApiKeyService.endpoints.updateRoleMasterApiKey.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateRoleMasterApiKeyMutation,
  useDeleteRoleMasterApiKeyMutation,
  useGetRoleMasterApiKeyQuery,
  useUpdateRoleMasterApiKeyMutation,
  // END OF EXPORTS
} = roleMasterApiKeyService

/* Usage examples:
const { data, isLoading } = useGetRoleMasterApiKeyQuery({ id: 2 }, {}) //get hook
const [createRoleMasterApiKey, { isLoading, data, isSuccess }] = useCreateRoleMasterApiKeyMutation() //create hook
roleMasterApiKeyService.endpoints.getRoleMasterApiKey.select({id: 2})(store.getState()) //access data from any function
*/
