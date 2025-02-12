import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const healthService = service
  .enhanceEndpoints({ addTagTypes: ['HealthEvents'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getHealthEvents: builder.query<
        Res['healthEvents'],
        Req['getHealthEvents']
      >({
        providesTags: [{ id: 'LIST', type: 'HealthEvents' }],
        query: (query: Req['getHealthEvents']) => ({
          url: `projects/${query.projectId}/feature-health/events/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getHealthEvents(
  store: any,
  data: Req['getHealthEvents'],
  options?: Parameters<
    typeof healthService.endpoints.getHealthEvents.initiate
  >[1],
) {
  return store.dispatch(
    healthService.endpoints.getHealthEvents.initiate(data, options),
  )
}

// END OF FUNCTION_EXPORTS

export const {
  useGetHealthEventsQuery,
  // END OF EXPORTS
} = healthService

/* Usage examples:
const { data, isLoading } = useGetHealthEventsQuery({ id: 2 }, {}) //get hook
healthService.endpoints.getHealthEvents.select({id: 2})(store.getState()) //access data from any function
*/
