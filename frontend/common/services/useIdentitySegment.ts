import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'
import transformCorePaging from 'common/transformCorePaging'
import { sortBy } from 'lodash'

export const identitySegmentService = service
  .enhanceEndpoints({ addTagTypes: ['IdentitySegment'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getIdentitySegments: builder.query<
        Res['identitySegments'],
        Req['getIdentitySegments']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'IdentitySegment' }],
        query: ({ projectId, ...query }: Req['getIdentitySegments']) => ({
          url: `/projects/${projectId}/segments/?${Utils.toParam(query)}`,
        }),
        transformResponse: (
          res: Res['identitySegments'],
          _,
          req: Req['getIdentitySegments'],
        ) =>
          transformCorePaging(req, {
            ...res,
            results: sortBy(res.results, 'name'),
          }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getIdentitySegments(
  store: any,
  data: Req['getIdentitySegments'],
  options?: Parameters<
    typeof identitySegmentService.endpoints.getIdentitySegments.initiate
  >[1],
) {
  return store.dispatch(
    identitySegmentService.endpoints.getIdentitySegments.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetIdentitySegmentsQuery,
  // END OF EXPORTS
} = identitySegmentService

/* Usage examples:
const { data, isLoading } = useGetIdentitySegmentsQuery({ id: 2 }, {}) //get hook
const [createIdentitySegments, { isLoading, data, isSuccess }] = useCreateIdentitySegmentsMutation() //create hook
identitySegmentService.endpoints.getIdentitySegments.select({id: 2})(store.getState()) //access data from any function
*/
