import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'

export const conversionEventService = service
  .enhanceEndpoints({ addTagTypes: ['ConversionEvent'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getConversionEvents: builder.query<
        Res['conversionEvents'],
        Req['getConversionEvents']
      >({
        providesTags: [{ id: 'LIST', type: 'ConversionEvent' }],
        query: (query) => {
          return {
            url: `conversion-event-types/?${Utils.toParam(query)}`,
          }
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getConversionEvents(
  store: any,
  data: Req['getConversionEvents'],
  options?: Parameters<
    typeof conversionEventService.endpoints.getConversionEvents.initiate
  >[1],
) {
  return store.dispatch(
    conversionEventService.endpoints.getConversionEvents.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetConversionEventsQuery,
  // END OF EXPORTS
} = conversionEventService

/* Usage examples:
const { data, isLoading } = useGetConversionEventsQuery({ id: 2 }, {}) //get hook
const [createConversionEvents, { isLoading, data, isSuccess }] = useCreateConversionEventsMutation() //create hook
conversionEventService.endpoints.getConversionEvents.select({id: 2})(store.getState()) //access data from any function
*/
