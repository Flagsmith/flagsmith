import { service } from 'common/service'
import { Req } from 'common/types/requests'
import { Res } from 'common/types/responses'
import Utils from 'common/utils/utils'

export const releasePipelinesService = service
  .enhanceEndpoints({ addTagTypes: ['ReleasePipelines'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      addFeatureToReleasePipeline: builder.mutation<
        Res['releasePipeline'],
        Req['addFeatureToReleasePipeline']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'ReleasePipelines' }],
        query: (query: Req['addFeatureToReleasePipeline']) => ({
          body: {
            feature_id: query.featureId,
          },
          method: 'POST',
          url: `projects/${query.projectId}/release-pipelines/${query.pipelineId}/add-feature/`,
        }),
      }),
      cloneReleasePipeline: builder.mutation<
        Res['releasePipeline'],
        Req['cloneReleasePipeline']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'ReleasePipelines' }],
        query: (query: Req['cloneReleasePipeline']) => ({
          method: 'POST',
          url: `projects/${query.projectId}/release-pipelines/${query.pipelineId}/clone/`,
        }),
      }),
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
      getReleasePipeline: builder.query<
        Res['releasePipeline'],
        Req['getReleasePipeline']
      >({
        providesTags: [{ type: 'ReleasePipelines' }],
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
      publishReleasePipeline: builder.mutation<
        Res['pipelineStages'],
        Req['publishReleasePipeline']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'ReleasePipelines' }],
        query: (query: Req['publishReleasePipeline']) => ({
          method: 'POST',
          url: `projects/${query.projectId}/release-pipelines/${query.pipelineId}/publish-pipeline/`,
        }),
      }),
      removeFeature: builder.mutation<
        Res['releasePipeline'],
        Req['removeFeatureFromReleasePipeline']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'ReleasePipelines' }],
        query: (query: Req['removeFeatureFromReleasePipeline']) => ({
          body: {
            feature_id: query.featureId,
          },
          method: 'POST',
          url: `projects/${query.projectId}/release-pipelines/${query.pipelineId}/remove-feature/`,
        }),
      }),
      updateReleasePipeline: builder.mutation<
        Res['releasePipeline'],
        Req['updateReleasePipeline']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'ReleasePipelines' },
          { id: res?.id, type: 'ReleasePipelines' },
        ],
        query: (query: Req['updateReleasePipeline']) => ({
          body: {
            description: query.description,
            name: query.name,
            stages: query.stages,
          },
          method: 'PUT',
          url: `projects/${query.project}/release-pipelines/${query.id}/`,
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

export async function removeFeatureFromReleasePipeline(
  store: any,
  data: Req['removeFeatureFromReleasePipeline'],
  options?: Parameters<
    typeof releasePipelinesService.endpoints.removeFeature.initiate
  >[1],
) {
  return store.dispatch(
    releasePipelinesService.endpoints.removeFeature.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useAddFeatureToReleasePipelineMutation,
  useCloneReleasePipelineMutation,
  useCreateReleasePipelineMutation,
  useDeleteReleasePipelineMutation,
  useGetReleasePipelineQuery,
  useGetReleasePipelinesQuery,
  usePublishReleasePipelineMutation,
  useRemoveFeatureMutation,
  useUpdateReleasePipelineMutation,
  // END OF EXPORTS
} = releasePipelinesService

/* Usage examples:
const { data, isLoading } = useGetReleasePipelinesQuery({ id: 2 }, {}) //get hook
const [createReleasePipelines, { isLoading, data, isSuccess }] = useCreateReleasePipelinesMutation() //create hook
releasePipelinesService.endpoints.getReleasePipelines.select({id: 2})(store.getState()) //access data from any function
*/
