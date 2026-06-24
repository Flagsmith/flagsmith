import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'
import transformCorePaging from 'common/transformCorePaging'

export const experimentService = service
  .enhanceEndpoints({
    addTagTypes: ['Experiment', 'ExperimentExposures', 'ExperimentResults'],
  })
  .injectEndpoints({
    endpoints: (builder) => ({
      completeExperiment: builder.mutation<
        Res['experiment'],
        Req['experimentAction']
      >({
        invalidatesTags: (_res, _err, { experimentId }) => [
          { id: experimentId, type: 'Experiment' },
          { id: 'LIST', type: 'Experiment' },
        ],
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
      getExperiment: builder.query<Res['experiment'], Req['getExperiment']>({
        providesTags: (_res, _err, { experimentId }) => [
          { id: experimentId, type: 'Experiment' },
        ],
        query: ({ environmentId, experimentId }) => ({
          url: `environments/${environmentId}/experiments/${experimentId}/`,
        }),
      }),
      getExperimentBayesianResults: builder.query<
        Res['experimentBayesianResults'] | null,
        Req['getExperimentBayesianResults']
      >({
        providesTags: (_res, _err, { experimentId }) => [
          { id: experimentId, type: 'ExperimentResults' },
        ],
        query: ({ environmentId, experimentId }) => ({
          url: `environments/${environmentId}/experiments/${experimentId}/results/`,
        }),
        transformResponse: (res: {
          results: Res['experimentBayesianResults'] | null
        }) => res.results,
      }),
      getExperimentExposures: builder.query<
        Res['experimentExposures'] | null,
        Req['getExperimentExposures']
      >({
        providesTags: (_res, _err, { experimentId }) => [
          { id: experimentId, type: 'ExperimentExposures' },
        ],
        query: ({ environmentId, experimentId }) => ({
          url: `environments/${environmentId}/experiments/${experimentId}/exposures/`,
        }),
        transformResponse: (res: {
          exposures: Res['experimentExposures'] | null
        }) => res.exposures,
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
        invalidatesTags: (_res, _err, { experimentId }) => [
          { id: experimentId, type: 'Experiment' },
          { id: 'LIST', type: 'Experiment' },
        ],
        query: ({ environmentId, experimentId }) => ({
          method: 'POST',
          url: `environments/${environmentId}/experiments/${experimentId}/pause/`,
        }),
      }),
      refreshExperimentBayesianResults: builder.mutation<
        void,
        Req['refreshExperimentBayesianResults']
      >({
        invalidatesTags: (_res, _err, { experimentId }) => [
          { id: experimentId, type: 'ExperimentResults' },
        ],
        query: ({ environmentId, experimentId }) => ({
          method: 'POST',
          url: `environments/${environmentId}/experiments/${experimentId}/results/refresh/`,
        }),
      }),
      refreshExperimentExposures: builder.mutation<
        Res['experimentExposures'],
        Req['refreshExperimentExposures']
      >({
        invalidatesTags: (_res, _err, { experimentId }) => [
          { id: experimentId, type: 'ExperimentExposures' },
        ],
        queryFn: async (
          { environmentId, experimentId },
          _api,
          _extraOptions,
          baseQuery,
        ) => {
          const result = await baseQuery({
            method: 'POST',
            url: `environments/${environmentId}/experiments/${experimentId}/exposures/refresh/`,
          })
          if (result.error) {
            const retryAfter =
              result.meta?.response?.headers?.get('Retry-After')
            return {
              error: {
                ...result.error,
                retryAfter: retryAfter ? parseInt(retryAfter, 10) : null,
              },
            }
          }
          return { data: result.data as Res['experimentExposures'] }
        },
      }),
      startExperiment: builder.mutation<
        Res['experiment'],
        Req['experimentAction']
      >({
        invalidatesTags: (_res, _err, { experimentId }) => [
          { id: experimentId, type: 'Experiment' },
          { id: 'LIST', type: 'Experiment' },
        ],
        query: ({ environmentId, experimentId }) => ({
          method: 'POST',
          url: `environments/${environmentId}/experiments/${experimentId}/start/`,
        }),
      }),
      updateExperiment: builder.mutation<
        Res['experiment'],
        Req['updateExperiment']
      >({
        invalidatesTags: (_res, _err, { experimentId }) => [
          { id: experimentId, type: 'Experiment' },
          { id: 'LIST', type: 'Experiment' },
        ],
        query: ({ body, environmentId, experimentId }) => ({
          body,
          method: 'PATCH',
          url: `environments/${environmentId}/experiments/${experimentId}/`,
        }),
      }),
    }),
  })

export const {
  useCompleteExperimentMutation,
  useCreateExperimentMutation,
  useDeleteExperimentMutation,
  useGetExperimentBayesianResultsQuery,
  useGetExperimentExposuresQuery,
  useGetExperimentQuery,
  useGetExperimentsQuery,
  usePauseExperimentMutation,
  useRefreshExperimentBayesianResultsMutation,
  useRefreshExperimentExposuresMutation,
  useStartExperimentMutation,
  useUpdateExperimentMutation,
} = experimentService
