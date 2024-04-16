import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import moment from 'moment'
import range from 'lodash/range'
import sortBy from 'lodash/sortBy'

export const featureUsageService = service
  .enhanceEndpoints({ addTagTypes: ['FeatureUsage'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getFeatureUsage: builder.query<
        Res['featureUsage'],
        Req['getFeatureUsage']
      >({
        providesTags: (res, _, req) => [
          { id: req.featureId, type: 'FeatureUsage' },
        ],
        query: (query: Req['getFeatureUsage']) => ({
          url: `projects/${query.projectId}/features/${query.featureId}/evaluation-data/?period=${query.period}&environment_id=${query.environmentId}`,
        }),
        transformResponse: (res: Res['featureUsage']) => {
          const firstResult = res[0]
          const lastResult = firstResult && res[res.length - 1]
          const diff = firstResult
            ? moment(lastResult.day, 'YYYY-MM-DD').diff(
                moment(firstResult.day, 'YYYY-MM-DD'),
                'days',
              )
            : 0
          if (firstResult && diff) {
            range(0, diff).map((v) => {
              const day = moment(firstResult.day)
                .add(v, 'days')
                .format('YYYY-MM-DD')
              if (!res.find((v) => v.day === day)) {
                res.push({
                  'count': 0,
                  day,
                })
              }
            })
          }
          return sortBy(res, (v) => moment(v.day, 'YYYY-MM-DD').valueOf()).map(
            (v) => ({
              ...v,
              day: moment(v.day, 'YYYY-MM-DD').format('Do MMM'),
            }),
          )
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getFeatureUsage(
  store: any,
  data: Req['getFeatureUsage'],
  options?: Parameters<
    typeof featureUsageService.endpoints.getFeatureUsage.initiate
  >[1],
) {
  return store.dispatch(
    featureUsageService.endpoints.getFeatureUsage.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetFeatureUsageQuery,
  // END OF EXPORTS
} = featureUsageService

/* Usage examples:
const { data, isLoading } = useGetFeatureUsageQuery({ id: 2 }, {}) //get hook
const [createFeatureUsage, { isLoading, data, isSuccess }] = useCreateFeatureUsageMutation() //create hook
featureUsageService.endpoints.getFeatureUsage.select({id: 2})(store.getState()) //access data from any function
*/
