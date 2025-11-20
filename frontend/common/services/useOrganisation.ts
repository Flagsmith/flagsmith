import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const organisationService = service
  .enhanceEndpoints({ addTagTypes: ['Organisation'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      deleteOrganisation: builder.mutation<void, Req['deleteOrganisation']>({
        invalidatesTags: [{ id: 'LIST', type: 'Organisation' }],
        query: ({ id }: Req['deleteOrganisation']) => ({
          method: 'DELETE',
          url: `organisations/${id}/`,
        }),
      }),
      getOrganisation: builder.query<
        Res['organisation'],
        Req['getOrganisation']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'Organisation' }],
        query: ({ id }: Req['getOrganisation']) => ({
          url: `organisations/${id}/`,
        }),
      }),
      getOrganisations: builder.query<
        Res['organisations'],
        Req['getOrganisations']
      >({
        providesTags: [{ id: 'LIST', type: 'Organisation' }],
        query: () => ({
          url: `organisations/`,
        }),
      }),
      updateOrganisation: builder.mutation<
        Res['organisation'],
        Req['updateOrganisation']
      >({
        invalidatesTags: (res) => [
          { id: res?.id, type: 'Organisation' },
          { id: 'LIST', type: 'Organisation' },
        ],
        async onQueryStarted({ body, id }, { dispatch, queryFulfilled }) {
          // Optimistic update - immediately update the cache
          const patchResult = dispatch(
            organisationService.util.updateQueryData(
              'getOrganisation',
              { id },
              (draft) => {
                Object.assign(draft, body)
              },
            ),
          )

          try {
            await queryFulfilled
          } catch {
            // Automatic rollback on error
            patchResult.undo()
          }
        },
        query: ({ body, id }: Req['updateOrganisation']) => ({
          body,
          method: 'PUT',
          url: `organisations/${id}/`,
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
  useDeleteOrganisationMutation,
  useGetOrganisationQuery,
  useGetOrganisationsQuery,
  useUpdateOrganisationMutation,
  // END OF EXPORTS
} = organisationService

/* Usage examples:
const { data, isLoading } = useGetOrganisationsQuery({ id: 2 }, {}) //get hook
const [createOrganisations, { isLoading, data, isSuccess }] = useCreateOrganisationsMutation() //create hook
organisationService.endpoints.getOrganisations.select({id: 2})(store.getState()) //access data from any function
*/
