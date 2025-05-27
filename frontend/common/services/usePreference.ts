import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const preferenceService = service
  .enhanceEndpoints({ addTagTypes: ['Preference'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getPreferences: builder.query<Res['preferences'], Req['getPreferences']>({
        providesTags: [{ id: 'LIST', type: 'Preference' }],
        query: () => ({
          url: `preferences`,
        }),
      }),
      updatePreferences: builder.mutation<
        Res['preferences'],
        Req['updatePreferences']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'Preference' },
          { id: res?.id, type: 'Preference' },
        ],
        query: (query: Req['updatePreferences']) => ({
          body: query,
          method: 'PUT',
          url: `preferences`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function updatePreferences(
  store: any,
  data: Req['updatePreferences'],
  options?: Parameters<
    typeof preferenceService.endpoints.updatePreferences.initiate
  >[1],
) {
  return store.dispatch(
    preferenceService.endpoints.updatePreferences.initiate(data, options),
  )
}
export async function getPreferences(
  store: any,
  data: Req['getPreferences'],
  options?: Parameters<
    typeof preferenceService.endpoints.getPreferences.initiate
  >[1],
) {
  return store.dispatch(
    preferenceService.endpoints.getPreferences.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetPreferencesQuery,
  useUpdatePreferencesMutation,
  // END OF EXPORTS
} = preferenceService

/* Usage examples:
const { data, isLoading } = useGetPreferencesQuery({ id: 2 }, {}) //get hook
const [createPreferences, { isLoading, data, isSuccess }] = useCreatePreferencesMutation() //create hook
preferenceService.endpoints.getPreferences.select({id: 2})(store.getState()) //access data from any function
*/
