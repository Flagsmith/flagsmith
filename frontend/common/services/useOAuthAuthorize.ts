import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const oauthAuthorizeService = service
  .enhanceEndpoints({ addTagTypes: ['OAuthAuthorize'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      processOAuthConsent: builder.mutation<
        Res['processOAuthConsent'],
        Req['processOAuthConsent']
      >({
        query: (body) => ({
          body,
          method: 'POST',
          url: 'oauth/authorize/',
        }),
      }),
      validateOAuthAuthorize: builder.query<
        Res['validateOAuthAuthorize'],
        Req['validateOAuthAuthorize']
      >({
        keepUnusedDataFor: 600,
        query: (params) => ({
          url: `oauth/authorize/?${new URLSearchParams(params).toString()}`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export const {
  useProcessOAuthConsentMutation,
  useValidateOAuthAuthorizeQuery,
  // END OF EXPORTS
} = oauthAuthorizeService
