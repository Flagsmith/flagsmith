import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'
import transformCorePaging from 'common/transformCorePaging'

export const experimentService = service
  .enhanceEndpoints({ addTagTypes: ['Experiment'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      completeExperiment: builder.mutation<
        Res['experiment'],
        Req['experimentAction']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'Experiment' }],
        query: ({ environmentId, experimentId }) => ({
          method: 'POST',
          url: `environments/${environmentId}/experiments/${experimentId}/complete/`,
        }),
      }),
      createExperiment: builder.mutation<
        Res['experiment'],
        Req['createExperiment']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'Experiment' }],
        query: ({ body, environmentId }) => ({
          body,
          method: 'POST',
          url: `environments/${environmentId}/experiments/`,
        }),
      }),
      deleteExperiment: builder.mutation<void, Req['deleteExperiment']>({
        invalidatesTags: [{ id: 'LIST', type: 'Experiment' }],
        query: ({ environmentId, experimentId }) => ({
          method: 'DELETE',
          url: `environments/${environmentId}/experiments/${experimentId}/`,
        }),
      }),
      getExperiments: builder.query<Res['experiments'], Req['getExperiments']>({
        providesTags: [{ id: 'LIST', type: 'Experiment' }],
        query: ({ environmentId, ...rest }) => ({
          url: `environments/${environmentId}/experiments/?${Utils.toParam(
            rest,
          )}`,
        }),
        transformResponse: (res, _, req) => transformCorePaging(req, res),
      }),
      pauseExperiment: builder.mutation<
        Res['experiment'],
        Req['experimentAction']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'Experiment' }],
        query: ({ environmentId, experimentId }) => ({
          method: 'POST',
          url: `environments/${environmentId}/experiments/${experimentId}/pause/`,
        }),
      }),
      startExperiment: builder.mutation<
        Res['experiment'],
        Req['experimentAction']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'Experiment' }],
        query: ({ environmentId, experimentId }) => ({
          method: 'POST',
          url: `environments/${environmentId}/experiments/${experimentId}/start/`,
        }),
      }),
    }),
  })

export const {
  useCompleteExperimentMutation,
  useCreateExperimentMutation,
  useDeleteExperimentMutation,
  useGetExperimentsQuery,
  usePauseExperimentMutation,
  useStartExperimentMutation,
} = experimentService
