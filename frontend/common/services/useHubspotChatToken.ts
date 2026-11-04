import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

// HubSpot tokens last 12 hours.
const HUBSPOT_CHAT_TOKEN_CACHE_SECONDS = 11 * 60 * 60

export const hubspotChatTokenService = service
  .enhanceEndpoints({ addTagTypes: ['HubspotChatToken'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getHubspotChatToken: builder.query<
        Res['hubspotChatToken'],
        Req['getHubspotChatToken']
      >({
        keepUnusedDataFor: HUBSPOT_CHAT_TOKEN_CACHE_SECONDS,
        providesTags: [{ id: 'ME', type: 'HubspotChatToken' }],
        query: () => ({
          url: `auth/users/me/hubspot-chat-token/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getHubspotChatToken(
  store: any,
  data: Req['getHubspotChatToken'],
  options?: Parameters<
    typeof hubspotChatTokenService.endpoints.getHubspotChatToken.initiate
  >[1],
) {
  return store.dispatch(
    hubspotChatTokenService.endpoints.getHubspotChatToken.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetHubspotChatTokenQuery,
  // END OF EXPORTS
} = hubspotChatTokenService
