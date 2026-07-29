import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'
import transformCursorPaging from 'common/transformCursorPaging'

export const segmentMembersService = service
  .enhanceEndpoints({ addTagTypes: ['SegmentMembers'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getSegmentMembers: builder.query<
        Res['segmentMembers'],
        Req['getSegmentMembers']
      >({
        providesTags: (_res, _err, arg) => [
          { id: arg.id, type: 'SegmentMembers' },
        ],
        query: ({ environment, id, page_size = 10, pages, projectId, q }) => {
          // The cursor for the current page is the last entry on the stack the
          // component has stepped through; the first page sends no cursor.
          const cursor = pages?.[pages.length - 1]
          return {
            url: `projects/${projectId}/segments/${id}/members/?${Utils.toParam(
              { cursor, environment, limit: page_size, q },
            )}`,
          }
        },
        transformResponse: (
          res: Res['segmentMembers'],
          _meta,
          req: Req['getSegmentMembers'],
        ) => transformCursorPaging(req, res),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getSegmentMembers(
  store: any,
  data: Req['getSegmentMembers'],
  options?: Parameters<
    typeof segmentMembersService.endpoints.getSegmentMembers.initiate
  >[1],
) {
  return store.dispatch(
    segmentMembersService.endpoints.getSegmentMembers.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetSegmentMembersQuery,
  // END OF EXPORTS
} = segmentMembersService

/* Usage examples:
const { data, isLoading } = useGetSegmentMembersQuery({ id: 2, projectId: 1, environment: 3 }, {}) //get hook
segmentMembersService.endpoints.getSegmentMembers.select({ id: 2, projectId: 1, environment: 3 })(store.getState()) //access data from any function
*/
