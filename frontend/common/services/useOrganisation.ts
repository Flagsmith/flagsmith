import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const organisationService = service
  .enhanceEndpoints({ addTagTypes: ['Organisation'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getOrganisations: builder.query<
        Res['organisations'],
        Req['getOrganisations']
      >({
        providesTags: [{ id: 'LIST', type: 'Organisation' }],
        query: () => ({
          url: `organisations/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getOrganisations(
  store: any,
  data: Req['getOrganisations'],
  options?: Parameters<
    typeof organisationService.endpoints.getOrganisations.initiate
  >[1],
) {
  store.dispatch(
    organisationService.endpoints.getOrganisations.initiate(data, options),
  )
  return Promise.all(
    store.dispatch(organisationService.util.getRunningQueriesThunk()),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetOrganisationsQuery,
  // END OF EXPORTS
} = organisationService

/* Usage examples:
const { data, isLoading } = useGetOrganisationsQuery({ id: 2 }, {}) //get hook
const [createOrganisations, { isLoading, data, isSuccess }] = useCreateOrganisationsMutation() //create hook
organisationService.endpoints.getOrganisations.select({id: 2})(store.getState()) //access data from any function
*/
