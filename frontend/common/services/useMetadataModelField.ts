import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const metadataModelFieldService = service
  .enhanceEndpoints({ addTagTypes: ['MetadataModelField'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createMetadataModelField: builder.mutation<
        Res['metadataModelField'],
        Req['createMetadataModelField']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'MetadataModelField' }],
        query: (query: Req['createMetadataModelField']) => ({
          body: query.body,
          method: 'POST',
          url: `organisations/${query.organisation_id}/metadata-model-fields/`,
        }),
      }),
      deleteMetadataModelField: builder.mutation<
        Res['metadataModelField'],
        Req['deleteMetadataModelField']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'MetadataModelField' }],
        query: (query: Req['deleteMetadataModelField']) => ({
          method: 'DELETE',
          url: `organisations/${query.organisation_id}/metadata-model-fields/${query.id}/`,
        }),
      }),
      getMetadataModelField: builder.query<
        Res['metadataModelField'],
        Req['getMetadataModelField']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'MetadataModelField' }],
        query: (query: Req['getMetadataModelField']) => ({
          url: `organisations/${query.organisation_id}/metadata-model-fields/${query.id}/`,
        }),
      }),
      getMetadataModelFieldList: builder.query<
        Res['metadataModelFieldList'],
        Req['getMetadataModelFields']
      >({
        providesTags: [{ id: 'LIST', type: 'MetadataModelField' }],
        query: (query: Req['getMetadataModelFields']) => ({
          url: `organisations/${query.organisation_id}/metadata-model-fields/`,
        }),
      }),
      updateMetadataModelField: builder.mutation<
        Res['metadataModelField'],
        Req['updateMetadataModelField']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'MetadataModelField' },
          { id: res?.id, type: 'MetadataModelField' },
        ],
        query: (query: Req['updateMetadataModelField']) => ({
          body: query.body,
          method: 'PUT',
          url: `organisations/${query.organisation_id}/metadata-model-fields/${query.id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createMetadataModelField(
  store: any,
  data: Req['createMetadataModelField'],
  options?: Parameters<
    typeof metadataModelFieldService.endpoints.createMetadataModelField.initiate
  >[1],
) {
  return store.dispatch(
    metadataModelFieldService.endpoints.createMetadataModelField.initiate(
      data,
      options,
    ),
  )
}
export async function deleteMetadataModelField(
  store: any,
  data: Req['deleteMetadataModelField'],
  options?: Parameters<
    typeof metadataModelFieldService.endpoints.deleteMetadataModelField.initiate
  >[1],
) {
  return store.dispatch(
    metadataModelFieldService.endpoints.deleteMetadataModelField.initiate(
      data,
      options,
    ),
  )
}
export async function getMetadataModelField(
  store: any,
  data: Req['getMetadataModelField'],
  options?: Parameters<
    typeof metadataModelFieldService.endpoints.getMetadataModelField.initiate
  >[1],
) {
  return store.dispatch(
    metadataModelFieldService.endpoints.getMetadataModelField.initiate(
      data,
      options,
    ),
  )
}
export async function getMetadataModelFieldList(
  store: any,
  data: Req['getMetadataModelFields'],
  options?: Parameters<
    typeof metadataModelFieldService.endpoints.getMetadataModelFieldList.initiate
  >[1],
) {
  return store.dispatch(
    metadataModelFieldService.endpoints.getMetadataModelFieldList.initiate(
      data,
      options,
    ),
  )
}
export async function updateMetadataModelField(
  store: any,
  data: Req['updateMetadataModelField'],
  options?: Parameters<
    typeof metadataModelFieldService.endpoints.updateMetadataModelField.initiate
  >[1],
) {
  return store.dispatch(
    metadataModelFieldService.endpoints.updateMetadataModelField.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateMetadataModelFieldMutation,
  useDeleteMetadataModelFieldMutation,
  useGetMetadataModelFieldListQuery,
  useGetMetadataModelFieldQuery,
  useUpdateMetadataModelFieldMutation,
  // END OF EXPORTS
} = metadataModelFieldService

/* Usage examples:
const { data, isLoading } = useGetMetadataModelFieldQuery({ id: 2 }, {}) //get hook
const [createMetadataModelField, { isLoading, data, isSuccess }] = useCreateMetadataModelFieldMutation() //create hook
metadataModelFieldService.endpoints.getMetadataModelField.select({id: 2})(store.getState()) //access data from any function
*/
