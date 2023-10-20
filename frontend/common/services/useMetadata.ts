import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const metadataService = service
  .enhanceEndpoints({ addTagTypes: ['Metadata'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createMetadata: builder.mutation<Res['metadata'], Req['createMetadata']>({
        invalidatesTags: [{ id: 'LIST', type: 'Metadata' }],
        query: (query: Req['createMetadata']) => ({
          body: query.body,
          method: 'POST',
          url: `metadata/fields/`,
        }),
      }),
      deleteMetadata: builder.mutation<Res['metadata'], Req['deleteMetadata']>({
        invalidatesTags: [{ id: 'LIST', type: 'Metadata' }],
        query: (query: Req['deleteMetadata']) => ({
          method: 'DELETE',
          url: `metadata/fields/${query.id}/`,
        }),
      }),
      getListMetadata: builder.query<Res['metadata'], Req['getMetadata']>({
        providesTags: (res) => [{ id: res?.id, type: 'Metadata' }],
        query: (query: Req['getMetadata']) => ({
          url: `metadata/fields/?${Utils.toParam(query)}`,
        }),
      }),
      getMetadata: builder.query<Res['metadata'], Req['getMetadata']>({
        providesTags: (res) => [{ id: res?.id, type: 'Metadata' }],
        query: (query: Req['getMetadata']) => ({
          url: `metadata/fields/${query.id}/`,
        }),
      }),
      updateMetadata: builder.mutation<Res['metadata'], Req['updateMetadata']>({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'Metadata' },
          { id: res?.id, type: 'Metadata' },
        ],
        query: (query: Req['updateMetadata']) => ({
          body: query.body,
          method: 'PUT',
          url: `metadata/fields/${query.id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createMetadata(
  store: any,
  data: Req['createMetadata'],
  options?: Parameters<
    typeof metadataService.endpoints.createMetadata.initiate
  >[1],
) {
  return store.dispatch(
    metadataService.endpoints.createMetadata.initiate(data, options),
  )
}
export async function deleteMetadata(
  store: any,
  data: Req['deleteMetadata'],
  options?: Parameters<
    typeof metadataService.endpoints.deleteMetadata.initiate
  >[1],
) {
  return store.dispatch(
    metadataService.endpoints.deleteMetadata.initiate(data, options),
  )
}
export async function getMetadata(
  store: any,
  data: Req['getMetadata'],
  options?: Parameters<
    typeof metadataService.endpoints.getMetadata.initiate
  >[1],
) {
  return store.dispatch(
    metadataService.endpoints.getMetadata.initiate(data, options),
  )
}
export async function getListMetadata(
  store: any,
  data: Req['getListMetadata'],
  options?: Parameters<
    typeof metadataService.endpoints.getListMetadata.initiate
  >[1],
) {
  return store.dispatch(
    metadataService.endpoints.getListMetadata.initiate(data, options),
  )
}
export async function updateMetadata(
  store: any,
  data: Req['updateMetadata'],
  options?: Parameters<
    typeof metadataService.endpoints.updateMetadata.initiate
  >[1],
) {
  return store.dispatch(
    metadataService.endpoints.updateMetadata.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateMetadataMutation,
  useDeleteMetadataMutation,
  useGetListMetadataQuery,
  useGetMetadataQuery,
  useUpdateMetadataMutation,
  // END OF EXPORTS
} = metadataService

/* Usage examples:
const { data, isLoading } = useGetMetadataQuery({ id: 2 }, {}) //get hook
const [createMetadata, { isLoading, data, isSuccess }] = useCreateMetadataMutation() //create hook
metadataService.endpoints.getMetadata.select({id: 2})(store.getState()) //access data from any function
*/
