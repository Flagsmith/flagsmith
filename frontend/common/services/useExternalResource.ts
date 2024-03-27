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
          url: `features/${query.feature_id}/external-resources/`,
        }),
      }),
      deleteExternalResource: builder.mutation<
        Res['externalResource'],
        Req['deleteExternalResource']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'ExternalResource' }],
        query: (query: Req['deleteExternalResource']) => ({
          method: 'DELETE',
          url: `features/${query.feature_id}/external-resources/${query.external_resource_id}/`,
        }),
      }),
      getExternalResources: builder.query<
        Res['externalResource'],
        Req['getExternalResources']
      >({
        providesTags: [{ id: 'LIST', type: 'ExternalResource' }],
        query: (query: Req['getExternalResources']) => ({
          url: `features/${query.feature_id}/external-resources/`,
        }),
      }),
      updateExternalResource: builder.mutation<
        Res['externalResource'],
        Req['updateExternalResource']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'ExternalResource' }],
        query: (query: Req['updateExternalResource']) => ({
          body: query,
          method: 'PUT',
          url: `external-resources/${query.external_resource_id}/`,
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
export async function getExternalResources(
  store: any,
  data: Req['getExternalResources'],
  options?: Parameters<
    typeof externalResourceService.endpoints.getExternalResources.initiate
  >[1],
) {
  return store.dispatch(
    externalResourceService.endpoints.getExternalResources.initiate(
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
  useGetExternalResourcesQuery,
  useUpdateExternalResourceMutation,
  // END OF EXPORTS
} = externalResourceService

/* Usage examples:
const { data, isLoading } = useGetExternalResourceQuery({ id: 2 }, {}) //get hook
const [createExternalResource, { isLoading, data, isSuccess }] = useCreateExternalResourceMutation() //create hook
externalResourceService.endpoints.getExternalResources.select({id: 2})(store.getState()) //access data from any function
*/
