import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const preferredToolService = service
  .enhanceEndpoints({ addTagTypes: ['PreferredTool'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      updatePreferredTools: builder.mutation<
        Res['preferredTools'],
        Req['updatePreferredTools']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'PreferredTool' },
          { id: res?.id, type: 'PreferredTool' },
        ],
        query: (query: Req['updatePreferredTools']) => ({
          body: query,
          method: 'PUT',
          url: `preferredTools/${query.id}`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function updatePreferredTools(
  store: any,
  data: Req['updatePreferredTools'],
  options?: Parameters<
    typeof preferredToolService.endpoints.updatePreferredTools.initiate
  >[1],
) {
  return store.dispatch(
    preferredToolService.endpoints.updatePreferredTools.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useUpdatePreferredToolsMutation,
  // END OF EXPORTS
} = preferredToolService

/* Usage examples:
const { data, isLoading } = useGetPreferredToolsQuery({ id: 2 }, {}) //get hook
const [createPreferredTools, { isLoading, data, isSuccess }] = useCreatePreferredToolsMutation() //create hook
preferredToolService.endpoints.getPreferredTools.select({id: 2})(store.getState()) //access data from any function
*/
