import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'

export const featureStateService = service
  .enhanceEndpoints({ addTagTypes: ['FeatureState'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getFeatureState: builder.query<
        Res['featureState'],
        Req['getFeatureState']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'FeatureState' }],
        query: (query: Req['getFeatureState']) => ({
          url: `environments/${query.environmentAPIKey}/featurestates/${query.id}/`,
        }),
      }),
      getFeatureStates: builder.query<
        Res['featureStates'],
        Req['getFeatureStates']
      >({
        providesTags: (req, _, query) => [
          {
            id: `LIST-${query.environmentAPIKey}-${query.feature}`,
            type: 'FeatureState',
          },
        ],
        query: ({ environmentAPIKey, ...query }) => ({
          url: `environments/${environmentAPIKey}/featurestates/?${Utils.toParam(
            query,
          )}`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getFeatureState(
  store: any,
  data: Req['getFeatureState'],
  options?: Parameters<
    typeof featureStateService.endpoints.getFeatureState.initiate
  >[1],
) {
  return store.dispatch(
    featureStateService.endpoints.getFeatureState.initiate(data, options),
  )
}
export async function getFeatureStates(
  store: any,
  data: Req['getFeatureStates'],
  options?: Parameters<
    typeof featureStateService.endpoints.getFeatureStates.initiate
  >[1],
) {
  return store.dispatch(
    featureStateService.endpoints.getFeatureStates.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetFeatureStateQuery,
  useGetFeatureStatesQuery,
  // END OF EXPORTS
} = featureStateService

/* Usage examples:
const { data, isLoading } = useGetFeatureStateQuery({ id: 2 }, {}) //get hook
const [createFeatureState, { isLoading, data, isSuccess }] = useCreateFeatureStateMutation() //create hook
featureStateService.endpoints.getFeatureState.select({id: 2})(store.getState()) //access data from any function
*/
