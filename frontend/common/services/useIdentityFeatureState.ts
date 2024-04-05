import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'

export const identityFeatureStateService = service
  .enhanceEndpoints({ addTagTypes: ['IdentityFeatureState'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getIdentityFeatureStates: builder.query<
        Res['identityFeatureStates'],
        Req['getIdentityFeatureStates']
      >({
        providesTags: [{ id: 'LIST', type: 'IdentityFeatureState' }],
        query: (query: Req['getIdentityFeatureStates']) => ({
          url: `environments/${
            query.environment_id
          }/${Utils.getIdentitiesEndpoint()}/${
            query.identity_id
          }/${Utils.getFeatureStatesEndpoint()}/`,
        }),
      }),
      getIdentityFeatureStatesAll: builder.query<
        Res['identityFeatureStates'],
        Req['getIdentityFeatureStatesAll']
      >({
        providesTags: (res, _, req) => [
          { id: req.user, type: 'IdentityFeatureState' },
        ],
        query: (query: Req['getIdentityFeatureStatesAll']) => ({
          url: `environments/${
            query.environment
          }/${Utils.getIdentitiesEndpoint()}/${
            query.user
          }/${Utils.getFeatureStatesEndpoint()}/all/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getIdentityFeatureStates(
  store: any,
  data: Req['getIdentityFeatureStates'],
  options?: Parameters<
    typeof identityFeatureStateService.endpoints.getIdentityFeatureStates.initiate
  >[1],
) {
  return store.dispatch(
    identityFeatureStateService.endpoints.getIdentityFeatureStates.initiate(
      data,
      options,
    ),
  )
}
export async function getIdentityFeatureStateAll(
  store: any,
  data: Req['getIdentityFeatureStatesAll'],
  options?: Parameters<
    typeof identityFeatureStateService.endpoints.getIdentityFeatureStatesAll.initiate
  >[1],
) {
  return store.dispatch(
    identityFeatureStateService.endpoints.getIdentityFeatureStatesAll.initiate(
      data,
      options,
    ),
  )
}

// END OF FUNCTION_EXPORTS

export const {
  useGetIdentityFeatureStatesAllQuery,
  useGetIdentityFeatureStatesQuery,
  // END OF EXPORTS
} = identityFeatureStateService

/* Usage examples:
const { data, isLoading } = useGetIdentityFeatureStatesQuery({ id: 2 }, {}) //get hook
const [createIdentityFeatureStates, { isLoading, data, isSuccess }] = useCreateIdentityFeatureStatesMutation() //create hook
identityFeatureStateService.endpoints.getIdentityFeatureStatesAll.select({id: 2})(store.getState()) //access data from any function
*/
