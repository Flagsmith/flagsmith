import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const emailActivationService = service
  .enhanceEndpoints({ addTagTypes: ['EmailActivation'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      activateAccount: builder.mutation<
        Res['activateAccount'],
        Req['activateAccount']
      >({
        query: (query: Req['activateAccount']) => ({
          body: query,
          method: 'POST',
          url: `auth/users/activation/`,
        }),
      }),
      resendActivationEmail: builder.mutation<
        Res['resendActivationEmail'],
        Req['resendActivationEmail']
      >({
        query: (query: Req['resendActivationEmail']) => ({
          body: query,
          method: 'POST',
          url: `auth/users/resend_activation/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function activateAccount(
  store: any,
  data: Req['activateAccount'],
  options?: Parameters<
    typeof emailActivationService.endpoints.activateAccount.initiate
  >[1],
) {
  return store.dispatch(
    emailActivationService.endpoints.activateAccount.initiate(data, options),
  )
}
export async function resendActivationEmail(
  store: any,
  data: Req['resendActivationEmail'],
  options?: Parameters<
    typeof emailActivationService.endpoints.resendActivationEmail.initiate
  >[1],
) {
  return store.dispatch(
    emailActivationService.endpoints.resendActivationEmail.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useActivateAccountMutation,
  useResendActivationEmailMutation,
  // END OF EXPORTS
} = emailActivationService
