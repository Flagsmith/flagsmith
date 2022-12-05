import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from '../utils/utils'
export const segmentService = service
  .enhanceEndpoints({ addTagTypes: ['Segment'] })
    .injectEndpoints({
  endpoints: (builder) => ({

    getSegments: builder.query<Res['segments'], Req['getSegments']>({
      query: ({projectId,...rest}) => ({
        url: `projects/${projectId}/segments/?${Utils.toParam(rest)}`,
      }),
      providesTags:[{ type: 'Segment', id: 'LIST' },],
    }),
    // END OF ENDPOINTS
  }),
 })

export async function getSegments(store: any, data: Req['getSegments'], options?: Parameters<typeof segmentService.endpoints.getSegments.initiate>[1]) {
  store.dispatch(segmentService.endpoints.getSegments.initiate(data,options))
  return Promise.all(store.dispatch(segmentService.util.getRunningQueriesThunk()))
}
  // END OF FUNCTION_EXPORTS

export const {
  useGetSegmentsQuery,
  // END OF EXPORTS
} = segmentService

// const { data, isLoading } = useGetSegmentsQuery({ id: 2 }, {}) get hook
// const [createSegments, { isLoading, data, isSuccess }] = useCreateSegmentsMutation() create hook
// segmentService.endpoints.getSegments.select({id: 2})(store.getState()) access data from any function
