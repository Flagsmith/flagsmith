import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'

export const changeRequestService = service
  .enhanceEndpoints({ addTagTypes: ['ChangeRequest'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getChangeRequests: builder.query<
        Res['changeRequests'],
        Req['getChangeRequests']
      >({
        providesTags: [{ id: 'LIST', type: 'ChangeRequest' }],
        query: ({ environmentId, ...rest }) => ({
          url: `environments/${environmentId}/list-change-requests/?${Utils.toParam(
            { ...rest },
          )}`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getChangeRequests(
  store: any,
  data: Req['getChangeRequests'],
  options?: Parameters<
    typeof changeRequestService.endpoints.getChangeRequests.initiate
  >[1],
) {
  return store.dispatch(
    changeRequestService.endpoints.getChangeRequests.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetChangeRequestsQuery,
  // END OF EXPORTS
} = changeRequestService

/* Usage examples:
const { data, isLoading } = useGetChangeRequestsQuery({ id: 2 }, {}) //get hook
const [createChangeRequests, { isLoading, data, isSuccess }] = useCreateChangeRequestsMutation() //create hook
changeRequestService.endpoints.getChangeRequests.select({id: 2})(store.getState()) //access data from any function
*/
