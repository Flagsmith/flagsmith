import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'
import transformCorePaging from 'common/transformCorePaging'
import { getStore } from 'common/store'
import { addVersionOfToSegment, segmentService } from './useSegment'

export const projectChangeRequestService = service
  .enhanceEndpoints({ addTagTypes: ['ProjectChangeRequest'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      actionProjectChangeRequest: builder.mutation<
        Res['projectChangeRequest'],
        Req['actionProjectChangeRequest']
      >({
        invalidatesTags: (_, _2, req) => [
          { id: `${req.id}`, type: 'ProjectChangeRequest' },
          { id: 'LIST', type: 'ProjectChangeRequest' },
        ],
        query: (query: Req['actionProjectChangeRequest']) => ({
          body: {},
          method: 'POST',
          url: `projects/${query.project_id}/change-requests/${query.id}/${query.actionType}/`,
        }),
        transformResponse: (response, _, req) => {
          getStore().dispatch(segmentService.util.invalidateTags(['Segment']))
          return response
        },
      }),
      createProjectChangeRequest: builder.mutation<
        Res['projectChangeRequest'],
        Req['createProjectChangeRequest']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'ProjectChangeRequest' }],
        queryFn: async (query, baseQueryApi, extraOptions, baseQuery) => {
          const result = await baseQuery({
            body: {
              ...query.data,
              segments: query.data.segments?.map(addVersionOfToSegment),
            },
            method: 'POST',
            url: `projects/${query.project_id}/change-requests/`,
          })
          return result
        },
      }),
      deleteProjectChangeRequest: builder.mutation<
        Res['projectChangeRequest'],
        Req['deleteProjectChangeRequest']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'ProjectChangeRequest' }],
        query: (query: Req['deleteProjectChangeRequest']) => ({
          body: query,
          method: 'DELETE',
          url: `projects/${query.project_id}/change-requests/${query.id}/`,
        }),
      }),
      getProjectChangeRequest: builder.query<
        Res['projectChangeRequest'],
        Req['getProjectChangeRequest']
      >({
        providesTags: (res) => [
          { id: `${res?.id}`, type: 'ProjectChangeRequest' },
        ],
        query: (query: Req['getProjectChangeRequest']) => ({
          url: `projects/${query.project_id}/change-requests/${query.id}/`,
        }),
      }),
      getProjectChangeRequests: builder.query<
        Res['projectChangeRequests'],
        Req['getProjectChangeRequests']
      >({
        providesTags: (res) => [{ id: 'LIST', type: 'ProjectChangeRequest' }],
        query: ({ project_id, ...rest }: Req['getProjectChangeRequests']) => ({
          url: `projects/${project_id}/change-requests/?${Utils.toParam({
            ...rest,
          })}`,
        }),
        transformResponse: (res, _, req) => transformCorePaging(req, res),
      }),
      updateProjectChangeRequest: builder.mutation<
        Res['projectChangeRequest'],
        Req['updateProjectChangeRequest']
      >({
        invalidatesTags: (res, _, req) => [
          { id: req.data.id, type: 'ProjectChangeRequest' },
          { id: 'LIST', type: 'ProjectChangeRequest' },
        ],
        query: (query: Req['updateProjectChangeRequest']) => ({
          body: query.data,
          method: 'PUT',
          url: `projects/${query.project_id}/change-requests/${query.data.id}/`,
        }),
      }),

      // END OF ENDPOINTS
    }),
  })

export async function createProjectChangeRequest(
  store: any,
  data: Req['createProjectChangeRequest'],
  options?: Parameters<
    typeof projectChangeRequestService.endpoints.createProjectChangeRequest.initiate
  >[1],
) {
  return store.dispatch(
    projectChangeRequestService.endpoints.createProjectChangeRequest.initiate(
      data,
      options,
    ),
  )
}

export async function updateProjectChangeRequest(
  store: any,
  data: Req['updateProjectChangeRequest'],
  options?: Parameters<
    typeof projectChangeRequestService.endpoints.updateProjectChangeRequest.initiate
  >[1],
) {
  return store.dispatch(
    projectChangeRequestService.endpoints.updateProjectChangeRequest.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useActionProjectChangeRequestMutation,
  useCreateProjectChangeRequestMutation,
  useDeleteProjectChangeRequestMutation,
  useGetProjectChangeRequestQuery,
  useGetProjectChangeRequestsQuery,
  useUpdateProjectChangeRequestMutation,
  // END OF EXPORTS
} = projectChangeRequestService

/* Usage examples:
const { data, isLoading } = useGetProjectChangeRequestsQuery({ id: 2 }, {}) //get hook
const [createProjectChangeRequest, { isLoading, data, isSuccess }] = useCreateProjectChangeRequestsMutation() //create hook
projectChangeRequestService.endpoints.getProjectChangeRequests.select({id: 2})(store.getState()) //access data from any function
*/
