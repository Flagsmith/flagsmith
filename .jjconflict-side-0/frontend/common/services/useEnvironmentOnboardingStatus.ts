import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const environmentOnboardingStatusService = service
  .enhanceEndpoints({ addTagTypes: ['EnvironmentOnboardingStatus'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getEnvironmentOnboardingStatus: builder.query<
        Res['environmentOnboardingStatus'],
        Req['getEnvironmentOnboardingStatus']
      >({
        providesTags: (res, err, req) => [
          { id: req.environmentKey, type: 'EnvironmentOnboardingStatus' },
        ],
        // Unauthenticated Core endpoint keyed by the environment's client-side
        // API key. Served by Core, not the edge/CDN host.
        query: (query: Req['getEnvironmentOnboardingStatus']) => ({
          url: `environments/${query.environmentKey}/onboarding-status/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getEnvironmentOnboardingStatus(
  store: any,
  data: Req['getEnvironmentOnboardingStatus'],
  options?: Parameters<
    typeof environmentOnboardingStatusService.endpoints.getEnvironmentOnboardingStatus.initiate
  >[1],
) {
  return store.dispatch(
    environmentOnboardingStatusService.endpoints.getEnvironmentOnboardingStatus.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetEnvironmentOnboardingStatusQuery,
  // END OF EXPORTS
} = environmentOnboardingStatusService

/* Usage examples:
const { data, isLoading } = useGetEnvironmentOnboardingStatusQuery({ environmentKey: 'abc' }, {}) //get hook
environmentOnboardingStatusService.endpoints.getEnvironmentOnboardingStatus.select({ environmentKey: 'abc' })(store.getState()) //access data from any function
*/
