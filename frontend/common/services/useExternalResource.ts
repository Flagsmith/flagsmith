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
          url: `projects/${query.project_id}/features/${query.feature_id}/feature-external-resources/`,
        }),
      }),
      deleteExternalResource: builder.mutation<
        Res['externalResource'],
        Req['deleteExternalResource']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'ExternalResource' }],
        query: (query: Req['deleteExternalResource']) => ({
          method: 'DELETE',
          url: `projects/${query.project_id}/features/${query.feature_id}/feature-external-resources/${query.external_resource_id}/`,
        }),
      }),
      getExternalResources: builder.query<
        Res['externalResource'],
        Req['getExternalResources']
      >({
        providesTags: [{ id: 'LIST', type: 'ExternalResource' }],
        query: (query: Req['getExternalResources']) => ({
          url: `projects/${query.project_id}/features/${query.feature_id}/feature-external-resources/`,
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
// END OF FUNCTION_EXPORTS

export const {
  useCreateExternalResourceMutation,
  useDeleteExternalResourceMutation,
  useGetExternalResourcesQuery,
  // END OF EXPORTS
} = externalResourceService

/* Usage examples:
const { data, isLoading } = useGetExternalResourceQuery({ id: 2 }, {}) //get hook
const [createExternalResource, { isLoading, data, isSuccess }] = useCreateExternalResourceMutation() //create hook
externalResourceService.endpoints.getExternalResources.select({id: 2})(store.getState()) //access data from any function
*/
