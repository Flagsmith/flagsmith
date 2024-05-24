import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const apiOrganisationUsageService = service
  .enhanceEndpoints({ addTagTypes: ['ApiOrganisationUsage'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getApiOrganisationUsage: builder.query<
        Res['apiOrganisationUsage'],
        Req['getApiOrganisationUsage']
      >({
        providesTags: [{ id: 'LIST', type: 'ApiOrganisationUsage' }],
        query: (query: Req['getApiOrganisationUsage']) => ({
          url: `organisations/${query.organisation_id}/api-usage-notification/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getApiOrganisationUsage(
  store: any,
  data: Req['getApiOrganisationUsage'],
  options?: Parameters<
    typeof apiOrganisationUsageService.endpoints.getApiOrganisationUsage.initiate
  >[1],
) {
  return store.dispatch(
    apiOrganisationUsageService.endpoints.getApiOrganisationUsage.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetApiOrganisationUsageQuery,
  // END OF EXPORTS
} = apiOrganisationUsageService

/* Usage examples:
const { data, isLoading } = useGetApiOrganisationUsageQuery({ id: 2 }, {}) //get hook
const [createApiOrganisationUsage, { isLoading, data, isSuccess }] = useCreateApiOrganisationUsageMutation() //create hook
apiOrganisationUsageService.endpoints.getApiOrganisationUsage.select({id: 2})(store.getState()) //access data from any function
*/
