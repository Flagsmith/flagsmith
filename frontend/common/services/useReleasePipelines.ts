import { service } from 'common/service'
import { Req } from 'common/types/requests'
import { Res } from 'common/types/responses'
import Utils from 'common/utils/utils'

export const releasePipelinesService = service
  .enhanceEndpoints({ addTagTypes: ['ReleasePipelines'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createReleasePipeline: builder.mutation<
        Res['releasePipeline'],
        Req['createReleasePipeline']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'ReleasePipelines' }],
        query: (query: Req['createReleasePipeline']) => ({
          body: {
            description: query.description,
            name: query.name,
            stages: query.stages,
          },
          method: 'POST',
          url: `projects/${query.project}/release-pipelines/`,
        }),
      }),
      deleteReleasePipeline: builder.mutation<{}, Req['deleteReleasePipeline']>(
        {
          invalidatesTags: [{ id: 'LIST', type: 'ReleasePipelines' }],
          query: (query: Req['deleteReleasePipeline']) => ({
            method: 'DELETE',
            url: `projects/${query.projectId}/release-pipelines/${query.pipelineId}/`,
          }),
        },
      ),
      getPipelineStage: builder.query<
        Res['pipelineStage'],
        Req['getPipelineStage']
      >({
        query: (query: Req['getPipelineStage']) => ({
          url: `projects/${query.projectId}/release-pipelines/${query.pipelineId}/stages/${query.stageId}/`,
        }),
      }),
      getPipelineStages: builder.query<
        Res['pipelineStages'],
        Req['getPipelineStages']
      >({
        query: ({
          pipelineId,
          projectId,
          ...rest
        }: Req['getPipelineStages']) => ({
          url: `projects/${projectId}/release-pipelines/${pipelineId}/stages/?${Utils.toParam(
            rest,
          )}`,
        }),
      }),
      getReleasePipeline: builder.query<
        Res['releasePipeline'],
        Req['getReleasePipeline']
      >({
        query: (query: Req['getReleasePipeline']) => ({
          url: `projects/${query.projectId}/release-pipelines/${query.pipelineId}/`,
        }),
      }),
      getReleasePipelines: builder.query<
        Res['releasePipelines'],
        Req['getReleasePipelines']
      >({
        providesTags: [{ id: 'LIST', type: 'ReleasePipelines' }],
        query: ({ projectId, ...rest }: Req['getReleasePipelines']) => ({
          url: `projects/${projectId}/release-pipelines/?${Utils.toParam(
            rest,
          )}`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getReleasePipelines(
  store: any,
  data: Req['getReleasePipelines'],
  options?: Parameters<
    typeof releasePipelinesService.endpoints.getReleasePipelines.initiate
  >[1],
) {
  return store.dispatch(
    releasePipelinesService.endpoints.getReleasePipelines.initiate(
      data,
      options,
    ),
  )
}

export async function createReleasePipeline(
  store: any,
  data: Req['createReleasePipeline'],
  options?: Parameters<
    typeof releasePipelinesService.endpoints.createReleasePipeline.initiate
  >[1],
) {
  return store.dispatch(
    releasePipelinesService.endpoints.createReleasePipeline.initiate(
      data,
      options,
    ),
  )
}

export async function getPipelineStages(
  store: any,
  data: Req['getPipelineStages'],
  options?: Parameters<
    typeof releasePipelinesService.endpoints.getPipelineStages.initiate
  >[1],
) {
  return store.dispatch(
    releasePipelinesService.endpoints.getPipelineStages.initiate(data, options),
  )
}

// END OF FUNCTION_EXPORTS

export const {
  useCreateReleasePipelineMutation,
  useDeleteReleasePipelineMutation,
  useGetPipelineStageQuery,
  useGetPipelineStagesQuery,
  useGetReleasePipelineQuery,
  useGetReleasePipelinesQuery,
  // END OF EXPORTS
} = releasePipelinesService

/* Usage examples:
const { data, isLoading } = useGetReleasePipelinesQuery({ id: 2 }, {}) //get hook
const [createReleasePipelines, { isLoading, data, isSuccess }] = useCreateReleasePipelinesMutation() //create hook
releasePipelinesService.endpoints.getReleasePipelines.select({id: 2})(store.getState()) //access data from any function
*/
