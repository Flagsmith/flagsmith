import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import { getProfile } from './useProfile'
import { getStore } from 'common/store'

export const onboardingService = service
  .enhanceEndpoints({ addTagTypes: ['Onboarding'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      updateOnboarding: builder.mutation<
        Res['onboarding'],
        Req['updateOnboarding']
      >({
        invalidatesTags: (res) => [{ id: 'LIST', type: 'Onboarding' }],
        query: (query: Req['updateOnboarding']) => ({
          body: query,
          method: 'PATCH',
          url: `auth/users/me/onboarding`,
        }),
        transformResponse: async (res) => {
          await getProfile(getStore(), {}, { forceRefetch: true })
          return res
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export async function updateOnboarding(
  store: any,
  data: Req['updateOnboarding'],
  options?: Parameters<
    typeof onboardingService.endpoints.updateOnboarding.initiate
  >[1],
) {
  return store.dispatch(
    onboardingService.endpoints.updateOnboarding.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useUpdateOnboardingMutation,
  // END OF EXPORTS
} = onboardingService

/* Usage examples:
const { data, isLoading } = useGetOnboardingQuery({ id: 2 }, {}) //get hook
const [createOnboarding, { isLoading, data, isSuccess }] = useCreateOnboardingMutation() //create hook
onboardingService.endpoints.getOnboarding.select({id: 2})(store.getState()) //access data from any function
*/
