import { Res } from 'common/types/responses';
import { Req } from 'common/types/requests';
import { service } from 'common/service';
import Utils from '../utils/utils';

export const segmentService = service
    .enhanceEndpoints({ addTagTypes: ['Segment'] })
    .injectEndpoints({
        endpoints: builder => ({
            getSegments: builder.query<Res['segments'], Req['getSegments']>({
                query: ({ projectId, ...rest }) => ({
                    url: `projects/${projectId}/segments/?${Utils.toParam(rest)}`,
                }),
                providesTags: (q, e, arg) => [{ type: 'Segment', id: `LIST${arg.projectId}` }],
            }),
            deleteSegment: builder.mutation<Res['segment'], Req['deleteSegment']>({
                query: (query: Req['deleteSegment']) => ({
                    url: `projects/${query.projectId}/segments/${query.id}/`,
                    method: 'DELETE',
                    body: query,
                }),
                invalidatesTags: (q, e, arg) => [{ type: 'Segment', id: `LIST${arg.projectId}` }],
            }),
            updateSegment: builder.mutation<Res['segment'], Req['updateSegment']>({
                query: (query: Req['updateSegment']) => ({
                    url: `projects/${query.projectId}/segments/${query.id}/`,
                    method: 'PUT',
                    body: query.segment,
                }),
                invalidatesTags: (q, e, arg) => [{ type: 'Segment', id: `LIST${arg.projectId}` }],
            }),
            createSegment: builder.mutation<Res['segment'], Req['createSegment']>({
                query: (query: Req['createSegment']) => ({
                    url: `projects/${query.projectId}/segments/`,
                    method: 'POST',
                    body: query,
                }),
                invalidatesTags: (q, e, arg) => [{ type: 'Segment', id: `LIST${arg.projectId}` }],
            }),
            // END OF ENDPOINTS
        }),
    });

export async function getSegments(store: any, data: Req['getSegments'], options?: Parameters<typeof segmentService.endpoints.getSegments.initiate>[1]) {
    store.dispatch(segmentService.endpoints.getSegments.initiate(data, options));
    return Promise.all(store.dispatch(segmentService.util.getRunningQueriesThunk()));
}
export async function deleteSegment(store: any, data: Req['deleteSegment'], options?: Parameters<typeof segmentService.endpoints.deleteSegment.initiate>[1]) {
    store.dispatch(segmentService.endpoints.deleteSegment.initiate(data, options));
    return Promise.all(store.dispatch(segmentService.util.getRunningQueriesThunk()));
}
export async function updateSegment(store: any, data: Req['updateSegment'], options?: Parameters<typeof segmentService.endpoints.updateSegment.initiate>[1]) {
    store.dispatch(segmentService.endpoints.updateSegment.initiate(data, options));
    return Promise.all(store.dispatch(segmentService.util.getRunningQueriesThunk()));
}
export async function createSegment(store: any, data: Req['createSegment'], options?: Parameters<typeof segmentService.endpoints.createSegment.initiate>[1]) {
    store.dispatch(segmentService.endpoints.createSegment.initiate(data, options));
    return Promise.all(store.dispatch(segmentService.util.getRunningQueriesThunk()));
}
// END OF FUNCTION_EXPORTS

export const {
    useGetSegmentsQuery,
    useDeleteSegmentMutation,
    useUpdateSegmentMutation,
    useCreateSegmentMutation,
    // END OF EXPORTS
} = segmentService;

/*
Usage examples:
const { data, isLoading } = useGetSegmentsQuery({ id: 2 }, {}) get hook
const [createSegments, { isLoading, data, isSuccess }] = useCreateSegmentsMutation() create hook
segmentService.endpoints.getSegments.select({id: 2})(store.getState()) access data from any function
*/
