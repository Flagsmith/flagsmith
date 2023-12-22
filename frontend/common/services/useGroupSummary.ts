import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const groupSummaryService = service
  .enhanceEndpoints({ addTagTypes: ['GroupSummary'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getGroupSummaries: builder.query<
        Res['groupSummaries'],
        Req['getGroupSummaries']
      >({
        providesTags: [{ id: 'LIST', type: 'GroupSummary' }],
        query: (query) => ({
          url: `organisations/${query.orgId}/groups/summaries/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getGroupSummaries(
  store: any,
  data: Req['getGroupSummaries'],
  options?: Parameters<
    typeof groupSummaryService.endpoints.getGroupSummaries.initiate
  >[1],
) {
  store.dispatch(
    groupSummaryService.endpoints.getGroupSummaries.initiate(data, options),
  )
  return Promise.all(
    store.dispatch(groupSummaryService.util.getRunningQueriesThunk()),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetGroupSummariesQuery,
  // END OF EXPORTS
} = groupSummaryService

/* Usage examples:
const { data, isLoading } = useGetGroupSummariesQuery({ id: 2 }, {}) //get hook
const [createGroupSummaries, { isLoading, data, isSuccess }] = useCreateGroupSummariesMutation() //create hook
groupSummaryService.endpoints.getGroupSummaries.select({id: 2})(store.getState()) //access data from any function
*/
