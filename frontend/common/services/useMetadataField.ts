import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'

export const metadataService = service
  .enhanceEndpoints({ addTagTypes: ['Metadata'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createMetadataField: builder.mutation<
        Res['metadataField'],
        Req['createMetadataField']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'Metadata' }],
        query: (query: Req['createMetadataField']) => ({
          body: query.body,
          method: 'POST',
          url: `metadata/fields/`,
        }),
      }),
      deleteMetadataField: builder.mutation<
        Res['metadataField'],
        Req['deleteMetadataField']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'Metadata' }],
        query: (query: Req['deleteMetadataField']) => ({
          method: 'DELETE',
          url: `metadata/fields/${query.id}/`,
        }),
      }),
      getMetadataField: builder.query<
        Res['metadataField'],
        Req['getMetadataField']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'Metadata' }],
        query: (query: Req['getMetadataField']) => ({
          url: `metadata/fields/${query.organisation_id}/`,
        }),
      }),
      getMetadataFieldList: builder.query<
        Res['metadataList'],
        Req['getMetadataList']
      >({
        providesTags: [{ id: 'LIST', type: 'Metadata' }],
        query: (query: Req['getMetadataList']) => ({
          url: `metadata/fields/?${Utils.toParam(query)}`,
        }),
      }),
      updateMetadataField: builder.mutation<
        Res['metadataField'],
        Req['updateMetadataField']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'Metadata' },
          { id: res?.id, type: 'Metadata' },
        ],
        query: (query: Req['updateMetadataField']) => ({
          body: query.body,
          method: 'PUT',
          url: `metadata/fields/${query.id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createMetadataField(
  store: any,
  data: Req['createMetadataField'],
  options?: Parameters<
    typeof metadataService.endpoints.createMetadataField.initiate
  >[1],
) {
  return store.dispatch(
    metadataService.endpoints.createMetadataField.initiate(data, options),
  )
}
export async function deleteMetadataField(
  store: any,
  data: Req['deleteMetadataField'],
  options?: Parameters<
    typeof metadataService.endpoints.deleteMetadataField.initiate
  >[1],
) {
  return store.dispatch(
    metadataService.endpoints.deleteMetadataField.initiate(data, options),
  )
}
export async function getMetadata(
  store: any,
  data: Req['getMetadataField'],
  options?: Parameters<
    typeof metadataService.endpoints.getMetadataField.initiate
  >[1],
) {
  return store.dispatch(
    metadataService.endpoints.getMetadataField.initiate(data, options),
  )
}
export async function getMetadataList(
  store: any,
  data: Req['getMetadataList'],
  options?: Parameters<
    typeof metadataService.endpoints.getMetadataFieldList.initiate
  >[1],
) {
  return store.dispatch(
    metadataService.endpoints.getMetadataFieldList.initiate(data, options),
  )
}
export async function updateMetadata(
  store: any,
  data: Req['updateMetadataField'],
  options?: Parameters<
    typeof metadataService.endpoints.updateMetadataField.initiate
  >[1],
) {
  return store.dispatch(
    metadataService.endpoints.updateMetadataField.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateMetadataFieldMutation,
  useDeleteMetadataFieldMutation,
  useGetMetadataFieldListQuery,
  useGetMetadataFieldQuery,
  useUpdateMetadataFieldMutation,
  // END OF EXPORTS
} = metadataService

/* Usage examples:
const { data, isLoading } = useGetMetadataFieldQuery({ id: 2 }, {}) //get hook
const [createMetadataField, { isLoading, data, isSuccess }] = useCreateMetadataFieldMutation() //create hook
metadataService.endpoints.getMetadataField.select({id: 2})(store.getState()) //access data from any function
*/
