import { Organisation, Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Constants from 'common/constants'
import API from 'project/api'
import AccountStore from 'common/stores/account-store'
import { getStore } from 'common/store'
import { organisationService } from './useOrganisation'

export const subscriptionService = service
  .enhanceEndpoints({ addTagTypes: ['UpdateSubscription'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createUpdateSubscription: builder.mutation<
        Res['updateSubscription'],
        Req['createUpdateSubscription']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'UpdateSubscription' }],
        query: ({
          organisationId,
          ...rest
        }: Req['createUpdateSubscription']) => ({
          body: { ...rest },
          method: 'POST',
          url: `organisations/${organisationId}/update-subscription/`,
        }),
        transformResponse: (res: Organisation) => {
          try {
            if (res && res.subscription && res.subscription.plan) {
              API.trackEvent(Constants.events.UPGRADE(res.subscription.plan))
              API.postEvent(res.subscription.plan, 'chargebee')
            }
          } catch (e) {}
          getStore().dispatch(
            organisationService.util.invalidateTags(['Organisation']),
          )

          //todo: remove when account-store is migrated
          AccountStore.getOrganisations().then(() => {
            AccountStore.saved()
          })

          return {}
        },
      }),
      getSubscription: builder.query<
        Res['subscription'],
        Req['getSubscription']
      >({
        providesTags: [{ id: 'LIST', type: 'UpdateSubscription' }],
        query: (query: Req['getSubscription']) => ({
          url: `organisations/${query.organisationId}/get-hosted-page-url-for-subscription-upgrade/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createUpdateSubscription(
  store: any,
  data: Req['createUpdateSubscription'],
  options?: Parameters<
    typeof subscriptionService.endpoints.createUpdateSubscription.initiate
  >[1],
) {
  return store.dispatch(
    subscriptionService.endpoints.createUpdateSubscription.initiate(
      data,
      options,
    ),
  )
}
export async function getSubscription(
  store: any,
  data: Req['getSubscription'],
  options?: Parameters<
    typeof subscriptionService.endpoints.getSubscription.initiate
  >[1],
) {
  return store.dispatch(
    subscriptionService.endpoints.getSubscription.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateUpdateSubscriptionMutation,
  useGetSubscriptionQuery,
  // END OF EXPORTS
} = subscriptionService

/* Usage examples:
const { data, isLoading } = useGetUpdateSubscriptionQuery({ id: 2 }, {}) //get hook
const [createUpdateSubscription, { isLoading, data, isSuccess }] = useCreateUpdateSubscriptionMutation() //create hook
subscriptionService.endpoints.getUpdateSubscription.select({id: 2})(store.getState()) //access data from any function
*/
