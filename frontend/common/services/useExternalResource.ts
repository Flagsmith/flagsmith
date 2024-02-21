import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const externalResourceService = service
  .enhanceEndpoints({ addTagTypes: ['ExternalResource'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createExternalResource: builder.mutation<
        Res['externalResource'],
        Req['createExternalResource']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'ExternalResource' }],
        query: (query: Req['createExternalResource']) => ({
          body: query.body,
          method: 'POST',
          url: `external-resources/`,
        }),
      }),
      deleteExternalResource: builder.mutation<
        Res['externalResource'],
        Req['deleteExternalResource']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'ExternalResource' }],
        query: (query: Req['deleteExternalResource']) => ({
          method: 'DELETE',
          url: `external-resources/${query.external_resource_id}/`,
        }),
      }),
      getExternalResource: builder.query<
        Res['externalResource'],
        Req['getExternalResource']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'ExternalResource' }],
        query: (query: Req['getExternalResource']) => ({
          url: `features/${query.feature_id}/external-resources/`,
        }),
      }),
      updateExternalResource: builder.mutation<
        Res['externalResource'],
        Req['updateExternalResource']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'ExternalResource' },
          { id: res?.id, type: 'ExternalResource' },
        ],
        query: (query: Req['updateExternalResource']) => ({
          body: query,
          method: 'PUT',
          url: `external-resources/${query.id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createExternalResource(
  store: any,
  data: Req['createExternalResource'],
  options?: Parameters<
    typeof externalResourceService.endpoints.createExternalResource.initiate
  >[1],
) {
  return store.dispatch(
    externalResourceService.endpoints.createExternalResource.initiate(
      data,
      options,
    ),
  )
}
export async function deleteExternalResource(
  store: any,
  data: Req['deleteExternalResource'],
  options?: Parameters<
    typeof externalResourceService.endpoints.deleteExternalResource.initiate
  >[1],
) {
  return store.dispatch(
    externalResourceService.endpoints.deleteExternalResource.initiate(
      data,
      options,
    ),
  )
}
export async function getExternalResource(
  store: any,
  data: Req['getExternalResource'],
  options?: Parameters<
    typeof externalResourceService.endpoints.getExternalResource.initiate
  >[1],
) {
  return store.dispatch(
    externalResourceService.endpoints.getExternalResource.initiate(
      data,
      options,
    ),
  )
}
export async function updateExternalResource(
  store: any,
  data: Req['updateExternalResource'],
  options?: Parameters<
    typeof externalResourceService.endpoints.updateExternalResource.initiate
  >[1],
) {
  return store.dispatch(
    externalResourceService.endpoints.updateExternalResource.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateExternalResourceMutation,
  useDeleteExternalResourceMutation,
  useGetExternalResourceQuery,
  useUpdateExternalResourceMutation,
  // END OF EXPORTS
} = externalResourceService

/* Usage examples:
const { data, isLoading } = useGetExternalResourceQuery({ id: 2 }, {}) //get hook
const [createExternalResource, { isLoading, data, isSuccess }] = useCreateExternalResourceMutation() //create hook
externalResourceService.endpoints.getExternalResource.select({id: 2})(store.getState()) //access data from any function
*/
