import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import moment from 'moment'

export const featureAnalyticsService = service
  .enhanceEndpoints({ addTagTypes: ['FeatureAnalytics'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getEnvironmentAnalytics: builder.query<
        Res['environmentAnalytics'],
        Req['getEnvironmentAnalytics']
      >({
        providesTags: (result, error, arg) => [
          {
            id: `${arg.project_id}-${arg.feature_id}-${arg.environment_id}-${arg.period}`,
            type: 'FeatureAnalytics',
          },
        ],
        query: (query) => ({
          url: `projects/${query.project_id}/features/${query.feature_id}/evaluation-data/?period=${query.period}&environment_id=${query.environment_id}`,
        }),
      }),
      getFeatureAnalytics: builder.query<
        Res['featureAnalytics'],
        Req['getFeatureAnalytics']
      >({
        providesTags: [{ id: 'LIST', type: 'FeatureAnalytics' }],
        queryFn: async (query, baseQueryApi) => {
          const responses = await Promise.all(
            query.environment_ids.map((environment_id) => {
              return baseQueryApi.dispatch(
                featureAnalyticsService.endpoints.getEnvironmentAnalytics.initiate(
                  {
                    environment_id,
                    feature_id: query.feature_id,
                    period: query.period,
                    project_id: query.project_id,
                  },
                ),
              )
            }),
          )

          const error = responses.find((response) => response.isError)?.error
          const today = moment().startOf('day')
          const startDate = moment(today).subtract(query.period - 1, 'days')

          // Pre-build one bucket per day with zero counts for each env, and
          // keep a `day → bucket` map so per-entry lookups below are O(1)
          // instead of O(days) via Array.find (matters for long periods and
          // high entry counts).
          type DayBucket = { day: string } & { [envId: string]: number }
          const preBuiltData: DayBucket[] = []
          const bucketByDay = new Map<string, DayBucket>()
          for (
            let date = startDate.clone();
            date.isSameOrBefore(today);
            date.add(1, 'days')
          ) {
            const day = date.format('Do MMM')
            const bucket: DayBucket = { day }
            query.environment_ids.forEach((envId) => {
              bucket[envId] = 0
            })
            preBuiltData.push(bucket)
            bucketByDay.set(day, bucket)
          }

          // Collect raw entries with labels intact for label-based grouping.
          // chartData aggregates by environment (existing behaviour),
          // rawEntries preserves per-SDK labels for stacked charts (#6067).
          const rawEntries: Res['environmentAnalytics'] = []

          responses.forEach((response, i) => {
            const environmentId = query.environment_ids[i]

            response.data?.forEach((entry) => {
              rawEntries.push(entry)
              const day = moment(entry.day).format('Do MMM')
              const bucket = bucketByDay.get(day)
              if (bucket) {
                bucket[environmentId] = entry.count
              }
            })
          })
          return {
            data: error
              ? { chartData: [], rawEntries: [] }
              : { chartData: preBuiltData, rawEntries },
            error,
          }
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getEnvironmentAnalytics(
  store: any,
  data: Req['getEnvironmentAnalytics'],
  options?: Parameters<
    typeof featureAnalyticsService.endpoints.getEnvironmentAnalytics.initiate
  >[1],
) {
  return store.dispatch(
    featureAnalyticsService.endpoints.getEnvironmentAnalytics.initiate(
      data,
      options,
    ),
  )
}
export async function getFeatureAnalytics(
  store: any,
  data: Req['getFeatureAnalytics'],
  options?: Parameters<
    typeof featureAnalyticsService.endpoints.getFeatureAnalytics.initiate
  >[1],
) {
  return store.dispatch(
    featureAnalyticsService.endpoints.getFeatureAnalytics.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetEnvironmentAnalyticsQuery,
  useGetFeatureAnalyticsQuery,
  // END OF EXPORTS
} = featureAnalyticsService

/* Usage examples:
const { data, isLoading } = useGetFeatureAnalyticsQuery({ id: 2 }, {}) //get hook
const [createFeatureAnalytics, { isLoading, data, isSuccess }] = useCreateFeatureAnalyticsMutation() //create hook
featureAnalyticsService.endpoints.getFeatureAnalytics.select({id: 2})(store.getState()) //access data from any function
*/
