import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const trustRelationshipService = service
  .enhanceEndpoints({
    addTagTypes: ['TrustRelationship'],
  })
  .injectEndpoints({
    endpoints: (builder) => ({
      createTrustRelationship: builder.mutation<
        Res['trustRelationship'],
        Req['createTrustRelationship']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'TrustRelationship' }],
        query: (query: Req['createTrustRelationship']) => ({
          body: query.body,
          method: 'POST',
          url: `organisations/${query.organisation_id}/trust-relationships/`,
        }),
      }),
      deleteTrustRelationship: builder.mutation<
        void,
        Req['deleteTrustRelationship']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'TrustRelationship' }],
        query: (query: Req['deleteTrustRelationship']) => ({
          method: 'DELETE',
          url: `organisations/${query.organisation_id}/trust-relationships/${query.id}/`,
        }),
      }),
      getTrustRelationships: builder.query<
        Res['trustRelationships'],
        Req['getTrustRelationships']
      >({
        providesTags: [{ id: 'LIST', type: 'TrustRelationship' }],
        query: (query: Req['getTrustRelationships']) => ({
          url: `organisations/${query.organisation_id}/trust-relationships/`,
        }),
      }),
      updateTrustRelationship: builder.mutation<
        Res['trustRelationship'],
        Req['updateTrustRelationship']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'TrustRelationship' },
          { id: res?.id, type: 'TrustRelationship' },
        ],
        query: (query: Req['updateTrustRelationship']) => ({
          body: query.body,
          method: 'PUT',
          url: `organisations/${query.organisation_id}/trust-relationships/${query.id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getTrustRelationships(
  store: any,
  data: Req['getTrustRelationships'],
  options?: Parameters<
    typeof trustRelationshipService.endpoints.getTrustRelationships.initiate
  >[1],
) {
  return store.dispatch(
    trustRelationshipService.endpoints.getTrustRelationships.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateTrustRelationshipMutation,
  useDeleteTrustRelationshipMutation,
  useGetTrustRelationshipsQuery,
  useUpdateTrustRelationshipMutation,
  // END OF EXPORTS
} = trustRelationshipService

/* Usage examples:
const { data, isLoading } = useGetTrustRelationshipsQuery({ organisation_id: 2 }) //get hook
const [createTrustRelationship, { isLoading, data, isSuccess }] = useCreateTrustRelationshipMutation() //create hook
trustRelationshipService.endpoints.getTrustRelationships.select({organisation_id: 2})(store.getState()) //access data from any function
*/
