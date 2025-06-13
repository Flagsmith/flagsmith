import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const profileService = service
  .enhanceEndpoints({ addTagTypes: ['Profile'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getProfile: builder.query<Res['profile'], Req['getProfile']>({
        providesTags: [{ id: 'LIST', type: 'Profile' }],
        query: (query) => ({
          url: `auth/users/${query.id ?? 'me'}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getProfile(
  store: any,
  data: Req['getProfile'],
  options?: Parameters<typeof profileService.endpoints.getProfile.initiate>[1],
) {
  return store.dispatch(
    profileService.endpoints.getProfile.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetProfileQuery,
  // END OF EXPORTS
} = profileService
