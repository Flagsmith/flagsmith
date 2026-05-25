import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const experimentService = service
  .enhanceEndpoints({ addTagTypes: ['Experiment'] })
  .injectEndpoints({
    endpoints: (builder) => ({
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
      getExperiments: builder.query<Res['experiments'], Req['getExperiments']>({
        providesTags: [{ id: 'LIST', type: 'Experiment' }],
        query: ({ environmentId }) => ({
          url: `environments/${environmentId}/experiments/`,
        }),
      }),
    }),
  })

export const { useCreateExperimentMutation, useGetExperimentsQuery } =
  experimentService
