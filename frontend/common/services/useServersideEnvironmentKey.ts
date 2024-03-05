import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const serversideEnvironmentKeyService = service
  .enhanceEndpoints({ addTagTypes: ['ServersideEnvironmentKey'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createServersideEnvironmentKeys: builder.mutation<
        Res['serversideEnvironmentKeys'],
        Req['createServersideEnvironmentKeys']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'ServersideEnvironmentKey' }],
        query: (query: Req['createServersideEnvironmentKeys']) => ({
          body: query.data,
          method: 'POST',
          url: `environments/${query.environmentId}/api-keys/`,
        }),
      }),
      deleteServersideEnvironmentKeys: builder.mutation<
        Res['serversideEnvironmentKeys'],
        Req['deleteServersideEnvironmentKeys']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'ServersideEnvironmentKey' }],
        query: (query: Req['deleteServersideEnvironmentKeys']) => ({
          body: query,
          method: 'DELETE',
          url: `environments/${query.environmentId}/api-keys/${query.id}/`,
        }),
      }),
      getServersideEnvironmentKeys: builder.query<
        Res['serversideEnvironmentKeys'],
        Req['getServersideEnvironmentKeys']
      >({
        providesTags: (res) => [
          { id: res?.id, type: 'ServersideEnvironmentKey' },
        ],
        query: (query: Req['getServersideEnvironmentKeys']) => ({
          url: `environments/${query.environmentId}/api-keys/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createServersideEnvironmentKeys(
  store: any,
  data: Req['createServersideEnvironmentKeys'],
  options?: Parameters<
    typeof serversideEnvironmentKeyService.endpoints.createServersideEnvironmentKeys.initiate
  >[1],
) {
  return store.dispatch(
    serversideEnvironmentKeyService.endpoints.createServersideEnvironmentKeys.initiate(
      data,
      options,
    ),
  )
}
export async function deleteServersideEnvironmentKeys(
  store: any,
  data: Req['deleteServersideEnvironmentKeys'],
  options?: Parameters<
    typeof serversideEnvironmentKeyService.endpoints.deleteServersideEnvironmentKeys.initiate
  >[1],
) {
  return store.dispatch(
    serversideEnvironmentKeyService.endpoints.deleteServersideEnvironmentKeys.initiate(
      data,
      options,
    ),
  )
}
export async function getServersideEnvironmentKeys(
  store: any,
  data: Req['getServersideEnvironmentKeys'],
  options?: Parameters<
    typeof serversideEnvironmentKeyService.endpoints.getServersideEnvironmentKeys.initiate
  >[1],
) {
  return store.dispatch(
    serversideEnvironmentKeyService.endpoints.getServersideEnvironmentKeys.initiate(
      data,
      options,
    ),
  )
}

// END OF FUNCTION_EXPORTS

export const {
  useCreateServersideEnvironmentKeysMutation,
  useDeleteServersideEnvironmentKeysMutation,
  useGetServersideEnvironmentKeysQuery,
  // END OF EXPORTS
} = serversideEnvironmentKeyService

/* Usage examples:
const { data, isLoading } = useGetServersideEnvironmentKeysQuery({ id: 2 }, {}) //get hook
const [createServersideEnvironmentKeys, { isLoading, data, isSuccess }] = useCreateServersideEnvironmentKeysMutation() //create hook
serversideEnvironmentKeyService.endpoints.getServersideEnvironmentKeys.select({id: 2})(store.getState()) //access data from any function
*/
