import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const samlAttributeMappingService = service
  .enhanceEndpoints({ addTagTypes: ['SamlAttributeMapping'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createSamlAttributeMapping: builder.mutation<
        Res['samlAttributeMapping'],
        Req['createSamlAttributeMapping']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'SamlAttributeMapping' }],
        query: (query: Req['createSamlAttributeMapping']) => ({
          body: query,
          method: 'POST',
          url: `auth/saml/attribute-mapping/`,
        }),
      }),
      deleteSamlAttributeMapping: builder.mutation<
        Res['samlAttributeMapping'],
        Req['deleteSamlAttributeMapping']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'SamlAttributeMapping' }],
        query: (query: Req['deleteSamlAttributeMapping']) => ({
          body: query,
          method: 'DELETE',
          url: `auth/saml/attribute-mapping/`,
        }),
      }),
      getSamlAttributeMapping: builder.query<
        Res['samlAttributeMapping'],
        Req['getSamlAttributeMapping']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'SamlAttributeMapping' }],
        query: (query: Req['getSamlAttributeMapping']) => ({
          url: `auth/saml/attribute-mapping/`,
        }),
      }),
      updateSamlAttributeMapping: builder.mutation<
        Res['samlAttributeMapping'],
        Req['updateSamlAttributeMapping']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'SamlAttributeMapping' },
          { id: res?.id, type: 'SamlAttributeMapping' },
        ],
        query: (query: Req['updateSamlAttributeMapping']) => ({
          body: query,
          method: 'PUT',
          url: `auth/saml/attribute-mapping/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createSamlAttributeMapping(
  store: any,
  data: Req['createSamlAttributeMapping'],
  options?: Parameters<
    typeof samlAttributeMappingService.endpoints.createSamlAttributeMapping.initiate
  >[1],
) {
  return store.dispatch(
    samlAttributeMappingService.endpoints.createSamlAttributeMapping.initiate(
      data,
      options,
    ),
  )
}
export async function deleteSamlAttributeMapping(
  store: any,
  data: Req['deleteSamlAttributeMapping'],
  options?: Parameters<
    typeof samlAttributeMappingService.endpoints.deleteSamlAttributeMapping.initiate
  >[1],
) {
  return store.dispatch(
    samlAttributeMappingService.endpoints.deleteSamlAttributeMapping.initiate(
      data,
      options,
    ),
  )
}
export async function getSamlAttributeMapping(
  store: any,
  data: Req['getSamlAttributeMapping'],
  options?: Parameters<
    typeof samlAttributeMappingService.endpoints.getSamlAttributeMapping.initiate
  >[1],
) {
  return store.dispatch(
    samlAttributeMappingService.endpoints.getSamlAttributeMapping.initiate(
      data,
      options,
    ),
  )
}
export async function updateSamlAttributeMapping(
  store: any,
  data: Req['updateSamlAttributeMapping'],
  options?: Parameters<
    typeof samlAttributeMappingService.endpoints.updateSamlAttributeMapping.initiate
  >[1],
) {
  return store.dispatch(
    samlAttributeMappingService.endpoints.updateSamlAttributeMapping.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateSamlAttributeMappingMutation,
  useDeleteSamlAttributeMappingMutation,
  useGetSamlAttributeMappingQuery,
  useUpdateSamlAttributeMappingMutation,
  // END OF EXPORTS
} = samlAttributeMappingService

/* Usage examples:
const { data, isLoading } = useGetSamlAttributeMappingQuery({ id: 2 }, {}) //get hook
const [createSamlAttributeMapping, { isLoading, data, isSuccess }] = useCreateSamlAttributeMappingMutation() //create hook
samlAttributeMappingService.endpoints.getSamlAttributeMapping.select({id: 2})(store.getState()) //access data from any function
*/
