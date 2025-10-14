import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import { sortBy } from 'lodash'
import moment from 'moment'
import range from 'lodash/range'

export const featureAnalyticsService = service
  .enhanceEndpoints({ addTagTypes: ['FeatureAnalytics'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getFeatureAnalytics: builder.query<
        Res['featureAnalytics'],
        Req['getFeatureAnalytics']
      >({
        providesTags: [{ id: 'LIST', type: 'FeatureAnalytics' }],
        queryFn: async (query, baseQueryApi, extraOptions, baseQuery) => {
          const responses = await Promise.all(
            query.environment_ids.map((environment_id) => {
              return baseQuery({
                url: `projects/${query.project_id}/features/${query.feature_id}/evaluation-data/?period=${query.period}&environment_id=${environment_id}`,
              })
            }),
          )

          const error = responses.find((v) => !!v.error)?.error
          const today = moment().startOf('day')
          const startDate = moment(today).subtract(query.period - 1, 'days')
          const preBuiltData: Res['featureAnalytics'] = []
          for (
            let date = startDate.clone();
            date.isSameOrBefore(today);
            date.add(1, 'days')
          ) {
            const dayObj: Res['featureAnalytics'][number] = {
              day: date.format('Do MMM'),
            }
            query.environment_ids.forEach((envId) => {
              dayObj[envId] = 0
            })
            preBuiltData.push(dayObj)
          }

          responses.forEach((response, i) => {
            const environment_id = query.environment_ids[i]

            response.data.forEach((entry: Res['featureAnalytics'][number]) => {
              const date = moment(entry.day).format('Do MMM')
              const dayEntry = preBuiltData.find((d) => d.day === date)
              if (dayEntry) {
                dayEntry[environment_id] = entry.count // Set count for specific environment ID
              }
            })
          })
          return {
            data: error ? [] : preBuiltData,
            error,
          }
        },
      }),
      // END OF ENDPOINTS
    }),
  })

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
  useGetFeatureAnalyticsQuery,
  // END OF EXPORTS
} = featureAnalyticsService

/* Usage examples:
const { data, isLoading } = useGetFeatureAnalyticsQuery({ id: 2 }, {}) //get hook
const [createFeatureAnalytics, { isLoading, data, isSuccess }] = useCreateFeatureAnalyticsMutation() //create hook
featureAnalyticsService.endpoints.getFeatureAnalytics.select({id: 2})(store.getState()) //access data from any function
*/
