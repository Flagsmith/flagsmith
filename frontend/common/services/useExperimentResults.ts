import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const experimentResultsService = service
  .enhanceEndpoints({ addTagTypes: ['ExperimentResults'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getExperimentResults: builder.query<
        Res['experimentResults'],
        Req['getExperimentResults']
      >({
        providesTags: [{ id: 'LIST', type: 'ExperimentResults' }],
        query: (query: Req['getExperimentResults']) => ({
          url: `environments/${query.environmentId}/experiments/results/?feature=${query.featureName}`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export const { useGetExperimentResultsQuery } = experimentResultsService
