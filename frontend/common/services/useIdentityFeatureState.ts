import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const identityFeatureStateService = service
  .enhanceEndpoints({ addTagTypes: ['IdentityFeatureState'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getIdentityFeatureState: builder.query<
        Res['identityFeatureState'],
        Req['getIdentityFeatureState']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'IdentityFeatureState' }],
        query: (query: Req['getIdentityFeatureState']) => ({
          url: `identityFeatureState/${query.id}`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getIdentityFeatureState(
  store: any,
  data: Req['getIdentityFeatureState'],
  options?: Parameters<
    typeof identityFeatureStateService.endpoints.getIdentityFeatureState.initiate
  >[1],
) {
  store.dispatch(
    identityFeatureStateService.endpoints.getIdentityFeatureState.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(identityFeatureStateService.util.getRunningQueriesThunk()),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetIdentityFeatureStateQuery,
  // END OF EXPORTS
} = identityFeatureStateService

/* Usage examples:
const { data, isLoading } = useGetIdentityFeatureStateQuery({ id: 2 }, {}) //get hook
const [createIdentityFeatureState, { isLoading, data, isSuccess }] = useCreateIdentityFeatureStateMutation() //create hook
identityFeatureStateService.endpoints.getIdentityFeatureState.select({id: 2})(store.getState()) //access data from any function
*/
