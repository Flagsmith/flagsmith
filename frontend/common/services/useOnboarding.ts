import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const onboardingService = service
  .enhanceEndpoints({ addTagTypes: ['Onboarding'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createOnboarding: builder.mutation<
        Res['onboarding'],
        Req['createOnboarding']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'Onboarding' }],
        query: (query: Req['createOnboarding']) => ({
          body: query,
          method: 'POST',
          url: `onboarding`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createOnboarding(
  store: any,
  data: Req['createOnboarding'],
  options?: Parameters<
    typeof onboardingService.endpoints.createOnboarding.initiate
  >[1],
) {
  return store.dispatch(
    onboardingService.endpoints.createOnboarding.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateOnboardingMutation,
  // END OF EXPORTS
} = onboardingService

/* Usage examples:
const { data, isLoading } = useGetOnboardingQuery({ id: 2 }, {}) //get hook
const [createOnboarding, { isLoading, data, isSuccess }] = useCreateOnboardingMutation() //create hook
onboardingService.endpoints.getOnboarding.select({id: 2})(store.getState()) //access data from any function
*/
