import {
  Res,
  Segment,
  SegmentCondition,
  SegmentRule,
} from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'
import transformCorePaging from 'common/transformCorePaging'

export function addVersionOfToSegment(segment: Segment): Segment {
  const cloneDeep = <T>(obj: T): T => JSON.parse(JSON.stringify(obj))

  const updatedSegment = cloneDeep(segment)

  const processCondition = (condition: SegmentCondition): SegmentCondition => {
    return {
      ...condition,
      version_of: condition.version_of || condition.id,
    }
  }

  const processRule = (rule: SegmentRule): SegmentRule => {
    return {
      ...rule,
      conditions: rule.conditions.map(processCondition),
      rules: rule.rules.map(processRule),
      version_of: rule.version_of || rule.id,
    }
  }

  return {
    ...updatedSegment,
    rules: updatedSegment.rules.map(processRule),
  }
}

export const segmentService = service
  .enhanceEndpoints({ addTagTypes: ['Segment'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      cloneSegment: builder.mutation<Res['segment'], Req['cloneSegment']>({
        invalidatesTags: (q, e, arg) => [
          { id: `LIST${arg.projectId}`, type: 'Segment' },
        ],
        query: (query: Req['cloneSegment']) => ({
          body: { name: query.name },
          method: 'POST',
          url: `projects/${query.projectId}/segments/${query.segmentId}/clone/`,
        }),
      }),
      createSegment: builder.mutation<Res['segment'], Req['createSegment']>({
        invalidatesTags: (q, e, arg) => [
          { id: `LIST${arg.projectId}`, type: 'Segment' },
        ],
        query: (query: Req['createSegment']) => ({
          body: query.segment,
          method: 'POST',
          url: `projects/${query.projectId}/segments/`,
        }),
      }),
      deleteSegment: builder.mutation<Res['segment'], Req['deleteSegment']>({
        invalidatesTags: (q, e, arg) => [
          { id: `LIST${arg.projectId}`, type: 'Segment' },
        ],
        query: (query: Req['deleteSegment']) => ({
          body: query,
          method: 'DELETE',
          url: `projects/${query.projectId}/segments/${query.id}/`,
        }),
      }),
      getSegment: builder.query<Res['segment'], Req['getSegment']>({
        providesTags: (res) => [{ id: res?.id, type: 'Segment' }],
        query: (query: Req['getSegment']) => ({
          url: `projects/${query.projectId}/segments/${query.id}/`,
        }),
      }),
      getSegments: builder.query<Res['segments'], Req['getSegments']>({
        providesTags: (q, e, arg) => [
          { id: `LIST${arg.projectId}`, type: 'Segment' },
        ],
        query: ({ projectId, ...rest }) => ({
          url: `projects/${projectId}/segments/?${Utils.toParam(rest)}`,
        }),
        transformResponse: (
          baseQueryReturnValue: Res['segments'],
          meta,
          req,
        ) => {
          return transformCorePaging(req, baseQueryReturnValue)
        },
      }),
      updateSegment: builder.mutation<Res['segment'], Req['updateSegment']>({
        invalidatesTags: (q, e, arg) => [
          { id: `LIST${arg.projectId}`, type: 'Segment' },
          { id: `${arg.segment.id}`, type: 'Segment' },
        ],
        queryFn: async (query, baseQueryApi, extraOptions, baseQuery) => {
          const result = await baseQuery({
            body: addVersionOfToSegment(query.segment),
            method: 'PUT',
            url: `projects/${query.projectId}/segments/${query.segment.id}/`,
          })
          return result
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getSegments(
  store: any,
  data: Req['getSegments'],
  options?: Parameters<typeof segmentService.endpoints.getSegments.initiate>[1],
) {
  return store.dispatch(
    segmentService.endpoints.getSegments.initiate(data, options),
  )
}
export async function deleteSegment(
  store: any,
  data: Req['deleteSegment'],
  options?: Parameters<
    typeof segmentService.endpoints.deleteSegment.initiate
  >[1],
) {
  return store.dispatch(
    segmentService.endpoints.deleteSegment.initiate(data, options),
  )
}
export async function updateSegment(
  store: any,
  data: Req['updateSegment'],
  options?: Parameters<
    typeof segmentService.endpoints.updateSegment.initiate
  >[1],
) {
  return store.dispatch(
    segmentService.endpoints.updateSegment.initiate(data, options),
  )
}
export async function createSegment(
  store: any,
  data: Req['createSegment'],
  options?: Parameters<
    typeof segmentService.endpoints.createSegment.initiate
  >[1],
) {
  return store.dispatch(
    segmentService.endpoints.createSegment.initiate(data, options),
  )
}
export async function getSegment(
  store: any,
  data: Req['getSegment'],
  options?: Parameters<typeof segmentService.endpoints.getSegment.initiate>[1],
) {
  return store.dispatch(
    segmentService.endpoints.getSegment.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCloneSegmentMutation,
  useCreateSegmentMutation,
  useDeleteSegmentMutation,
  useGetSegmentQuery,
  useGetSegmentsQuery,
  useUpdateSegmentMutation,
  // END OF EXPORTS
} = segmentService

/*
Usage examples:
const { data, isLoading } = useGetSegmentsQuery({ id: 2 }, {}) get hook
const [createSegments, { isLoading, data, isSuccess }] = useCreateSegmentsMutation() create hook
segmentService.endpoints.getSegments.select({id: 2})(store.getState()) access data from any function
*/
