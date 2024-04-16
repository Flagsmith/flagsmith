import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'

export const identityFeatureStateService = service
  .enhanceEndpoints({ addTagTypes: ['IdentityFeatureState'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createCloneIdentityFeatureStates: builder.mutation<
        Res['cloneidentityFeatureStates'],
        Req['createCloneIdentityFeatureStates']
      >({
        invalidatesTags: [{ type: 'IdentityFeatureState' }],
        query: (query: Req['createCloneIdentityFeatureStates']) => ({
          body: query.body,
          method: 'POST',
          url: `environments/${
            query.environment_id
          }/${Utils.getIdentitiesEndpoint()}/${
            query.identity_id
          }/${Utils.getFeatureStatesEndpoint()}/clone-from-given-identity/`,
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

export async function createIdentityFeatureStates(
  store: any,
  data: Req['createCloneIdentityFeatureStates'],
  options?: Parameters<
    typeof identityFeatureStateService.endpoints.createCloneIdentityFeatureStates.initiate
  >[1],
) {
  return store.dispatch(
    identityFeatureStateService.endpoints.createCloneIdentityFeatureStates.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateCloneIdentityFeatureStatesMutation,
  useGetIdentityFeatureStatesAllQuery,
  // END OF EXPORTS
} = identityFeatureStateService

/* Usage examples:
const { data, isLoading } = useGetIdentityFeatureStatesQuery({ id: 2 }, {}) //get hook
const [createIdentityFeatureStates, { isLoading, data, isSuccess }] = useCreateIdentityFeatureStatesMutation() //create hook
identityFeatureStateService.endpoints.getIdentityFeatureStatesAll.select({id: 2})(store.getState()) //access data from any function
*/
