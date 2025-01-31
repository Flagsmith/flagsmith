import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const healthProviderService = service
  .enhanceEndpoints({ addTagTypes: ['HealthProviders'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createHealthProvider: builder.mutation<
        Res['healthProvider'],
        Req['createHealthProvider']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'HealthProviders' }],
        query: (query: Req['createHealthProvider']) => ({
          body: { name: query.name },
          method: 'POST',
          url: `projects/${query.projectId}/feature-health/providers/`,
        }),
      }),
      deleteHealthProvider: builder.mutation<void, Req['deleteHealthProvider']>(
        {
          invalidatesTags: [{ id: 'LIST', type: 'HealthProviders' }],
          query: (query: Req['deleteHealthProvider']) => ({
            method: 'DELETE',
            url: `projects/${query.projectId}/feature-health/providers/${query.providerId}/`,
          }),
        },
      ),
      getHealthProviders: builder.query<
        Res['healthProviders'],
        Req['getHealthProviders']
      >({
        providesTags: [{ id: 'LIST', type: 'HealthProviders' }],
        query: (query: Req['getHealthProviders']) => ({
          url: `projects/${query.projectId}/feature-health/providers/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getHealthProviders(
  store: any,
  data: Req['getHealthProviders'],
  options?: Parameters<
    typeof healthProviderService.endpoints.getHealthProviders.initiate
  >[1],
) {
  return store.dispatch(
    healthProviderService.endpoints.getHealthProviders.initiate(data, options),
  )
}

export async function createHealthProvider(
  store: any,
  data: Req['createHealthProvider'],
  options?: Parameters<
    typeof healthProviderService.endpoints.createHealthProvider.initiate
  >[1],
) {
  return store.dispatch(
    healthProviderService.endpoints.createHealthProvider.initiate(
      data,
      options,
    ),
  )
}

export async function deleteHealthProvider(
  store: any,
  data: Req['deleteHealthProvider'],
  options?: Parameters<
    typeof healthProviderService.endpoints.deleteHealthProvider.initiate
  >[1],
) {
  return store.dispatch(
    healthProviderService.endpoints.deleteHealthProvider.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateHealthProviderMutation,
  useDeleteHealthProviderMutation,
  useGetHealthProvidersQuery,
  // END OF EXPORTS
} = healthProviderService

/* Usage examples:
const { data, isLoading } = useGetHealthProvidersQuery({ id: 2 }, {}) //get hook
healthProviderService.endpoints.getHealthProviders.select({id: 2})(store.getState()) //access data from any function
*/
