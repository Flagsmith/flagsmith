import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const onboardingSupportOptInService = service
  .enhanceEndpoints({ addTagTypes: ['OnboardingSupportOptIn'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createOnboardingSupportOptIn: builder.mutation<
        Res['onboardingSupportOptIn'],
        Req['createOnboardingSupportOptIn']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'OnboardingSupportOptIn' }],
        query: (query: Req['createOnboardingSupportOptIn']) => ({
          body: query,
          method: 'POST',
          url: `onboarding/request/send/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createOnboardingSupportOptIn(
  store: any,
  data: Req['createOnboardingSupportOptIn'],
  options?: Parameters<
    typeof onboardingSupportOptInService.endpoints.createOnboardingSupportOptIn.initiate
  >[1],
) {
  return store.dispatch(
    onboardingSupportOptInService.endpoints.createOnboardingSupportOptIn.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateOnboardingSupportOptInMutation,
  // END OF EXPORTS
} = onboardingSupportOptInService

/* Usage examples:
const { data, isLoading } = useGetOnboardingSupportOptInQuery({ id: 2 }, {}) //get hook
const [createOnboardingSupportOptIn, { isLoading, data, isSuccess }] = useCreateOnboardingSupportOptInMutation() //create hook
onboardingSupportOptInService.endpoints.getOnboardingSupportOptIn.select({id: 2})(store.getState()) //access data from any function
*/
