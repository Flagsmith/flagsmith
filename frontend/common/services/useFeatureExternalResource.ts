import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const featureExternalResourceService = service
  .enhanceEndpoints({ addTagTypes: ['FeatureExternalResource'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createFeatureExternalResource: builder.mutation<
        Res['featureExternalResource'],
        Req['createFeatureExternalResource']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'FeatureExternalResource' }],
        query: (query: Req['createFeatureExternalResource']) => ({
          body: query.body,
          method: 'POST',
          url: `external-resources/${query.external_resource_pk}/features-external-resources/`,
        }),
      }),
      deleteFeatureExternalResource: builder.mutation<
        Res['featureExternalResource'],
        Req['deleteFeatureExternalResource']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'FeatureExternalResource' }],
        query: (query: Req['deleteFeatureExternalResource']) => ({
          method: 'DELETE',
          url: `external-resources/${query.external_resource_pk}/features-external-resources/${query.feature_external_resource_id}/`,
        }),
      }),
      getFeatureExternalResource: builder.query<
        Res['featureExternalResource'],
        Req['getFeatureExternalResource']
      >({
        providesTags: (res) => [
          { id: res?.id, type: 'FeatureExternalResource' },
        ],
        query: (query: Req['getFeatureExternalResource']) => ({
          url: `external-resources/${query.external_resource_pk}/features-external-resources/`,
        }),
      }),
      updateFeatureExternalResource: builder.mutation<
        Res['featureExternalResource'],
        Req['updateFeatureExternalResource']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'FeatureExternalResource' },
          { id: res?.id, type: 'FeatureExternalResource' },
        ],
        query: (query: Req['updateFeatureExternalResource']) => ({
          body: query,
          method: 'PUT',
          url: `external-resources/${query.external_resource_pk}/features-external-resources/${query.feature_external_resource_id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createFeatureExternalResource(
  store: any,
  data: Req['createFeatureExternalResource'],
  options?: Parameters<
    typeof featureExternalResourceService.endpoints.createFeatureExternalResource.initiate
  >[1],
) {
  return store.dispatch(
    featureExternalResourceService.endpoints.createFeatureExternalResource.initiate(
      data,
      options,
    ),
  )
}
export async function deleteFeatureExternalResource(
  store: any,
  data: Req['deleteFeatureExternalResource'],
  options?: Parameters<
    typeof featureExternalResourceService.endpoints.deleteFeatureExternalResource.initiate
  >[1],
) {
  return store.dispatch(
    featureExternalResourceService.endpoints.deleteFeatureExternalResource.initiate(
      data,
      options,
    ),
  )
}
export async function getFeatureExternalResource(
  store: any,
  data: Req['getFeatureExternalResource'],
  options?: Parameters<
    typeof featureExternalResourceService.endpoints.getFeatureExternalResource.initiate
  >[1],
) {
  return store.dispatch(
    featureExternalResourceService.endpoints.getFeatureExternalResource.initiate(
      data,
      options,
    ),
  )
}
export async function updateFeatureExternalResource(
  store: any,
  data: Req['updateFeatureExternalResource'],
  options?: Parameters<
    typeof featureExternalResourceService.endpoints.updateFeatureExternalResource.initiate
  >[1],
) {
  return store.dispatch(
    featureExternalResourceService.endpoints.updateFeatureExternalResource.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateFeatureExternalResourceMutation,
  useDeleteFeatureExternalResourceMutation,
  useGetFeatureExternalResourceQuery,
  useUpdateFeatureExternalResourceMutation,
  // END OF EXPORTS
} = featureExternalResourceService

/* Usage examples:
const { data, isLoading } = useGetFeatureExternalResourceQuery({ id: 2 }, {}) //get hook
const [createFeatureExternalResource, { isLoading, data, isSuccess }] = useCreateFeatureExternalResourceMutation() //create hook
featureExternalResourceService.endpoints.getFeatureExternalResource.select({id: 2})(store.getState()) //access data from any function
*/
