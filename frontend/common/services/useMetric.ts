import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'
import transformCorePaging from 'common/transformCorePaging'

export const metricService = service
  .enhanceEndpoints({ addTagTypes: ['Metric'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createMetric: builder.mutation<Res['metric'], Req['createMetric']>({
        invalidatesTags: [{ id: 'LIST', type: 'Metric' }],
        query: ({ body, environmentId }) => ({
          body,
          method: 'POST',
          url: `environments/${environmentId}/experiment-metrics/`,
        }),
      }),
      deleteMetric: builder.mutation<void, Req['deleteMetric']>({
        invalidatesTags: [{ id: 'LIST', type: 'Metric' }],
        query: ({ environmentId, metricId }) => ({
          method: 'DELETE',
          url: `environments/${environmentId}/experiment-metrics/${metricId}/`,
        }),
      }),
      getMetrics: builder.query<Res['metrics'], Req['getMetrics']>({
        providesTags: [{ id: 'LIST', type: 'Metric' }],
        query: ({ environmentId, ...rest }) => ({
          url: `environments/${environmentId}/experiment-metrics/?${Utils.toParam(
            rest,
          )}`,
        }),
        transformResponse: (res, _, req) => transformCorePaging(req, res),
      }),
    }),
  })

export const {
  useCreateMetricMutation,
  useDeleteMetricMutation,
  useGetMetricsQuery,
} = metricService
