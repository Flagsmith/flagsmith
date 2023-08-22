import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'

export const organisationUsageService = service
  .enhanceEndpoints({ addTagTypes: ['OrganisationUsage'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getOrganisationUsage: builder.query<
        Res['organisationUsage'],
        Req['getOrganisationUsage']
      >({
        providesTags: () => [{ id: 'LIST', type: 'OrganisationUsage' }],
        query: (query: Req['getOrganisationUsage']) => {
          return {
            url: `organisations/${
              query.organisationId
            }/usage-data/?${Utils.toParam({
              environment_id: query.environmentId,
              project_id: query.projectId,
            })}`,
          }
        },
        transformResponse: (data: Res['organisationUsage']['events_list']) => {
          let flags = 0
          let traits = 0
          let environmentDocument = 0
          let identities = 0
          data?.map((v) => {
            flags += v.flags || 0
            traits += v.traits || 0
            environmentDocument += v.environment_document || 0
            identities += v.identities || 0
          })
          return {
            events_list: data,
            totals: {
              environmentDocument,
              flags,
              identities,
              total: flags + traits + environmentDocument + identities,
              traits,
            },
          }
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getOrganisationUsage(
  store: any,
  data: Req['getOrganisationUsage'],
  options?: Parameters<
    typeof organisationUsageService.endpoints.getOrganisationUsage.initiate
  >[1],
) {
  return store.dispatch(
    organisationUsageService.endpoints.getOrganisationUsage.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetOrganisationUsageQuery,
  // END OF EXPORTS
} = organisationUsageService

/* Usage examples:
const { data, isLoading } = useGetOrganisationUsageQuery({ id: 2 }, {}) //get hook
const [createOrganisationUsage, { isLoading, data, isSuccess }] = useCreateOrganisationUsageMutation() //create hook
organisationUsageService.endpoints.getOrganisationUsage.select({id: 2})(store.getState()) //access data from any function
*/
