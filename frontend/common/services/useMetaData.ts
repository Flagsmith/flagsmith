import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const metaDataService = service
  .enhanceEndpoints({ addTagTypes: ['MetaData'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createMetaData: builder.mutation<Res['metaData'], Req['createMetaData']>({
        invalidatesTags: [{ id: 'LIST', type: 'MetaData' }],
        query: (query: Req['createMetaData']) => ({
          body: query.body,
          method: 'POST',
          url: `metadata/fields/`,
        }),
      }),
      deleteMetaData: builder.mutation<Res['metaData'], Req['deleteMetaData']>({
        invalidatesTags: [{ id: 'LIST', type: 'MetaData' }],
        query: (query: Req['deleteMetaData']) => ({
          method: 'DELETE',
          url: `metadata/fields/${query.id}/`,
        }),
      }),
      getListMetaData: builder.query<Res['metaData'], Req['getMetaData']>({
        providesTags: (res) => [{ id: res?.id, type: 'MetaData' }],
        query: (query: Req['getMetaData']) => ({
          url: `metadata/fields/?${Utils.toParam(query)}`,
        }),
      }),
      getMetaData: builder.query<Res['metaData'], Req['getMetaData']>({
        providesTags: (res) => [{ id: res?.id, type: 'MetaData' }],
        query: (query: Req['getMetaData']) => ({
          url: `metadata/fields/${query.id}/`,
        }),
      }),
      updateMetaData: builder.mutation<Res['metaData'], Req['updateMetaData']>({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'MetaData' },
          { id: res?.id, type: 'MetaData' },
        ],
        query: (query: Req['updateMetaData']) => ({
          body: query.body,
          method: 'PUT',
          url: `metadata/fields/${query.id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createMetaData(
  store: any,
  data: Req['createMetaData'],
  options?: Parameters<
    typeof metaDataService.endpoints.createMetaData.initiate
  >[1],
) {
  return store.dispatch(
    metaDataService.endpoints.createMetaData.initiate(data, options),
  )
}
export async function deleteMetaData(
  store: any,
  data: Req['deleteMetaData'],
  options?: Parameters<
    typeof metaDataService.endpoints.deleteMetaData.initiate
  >[1],
) {
  return store.dispatch(
    metaDataService.endpoints.deleteMetaData.initiate(data, options),
  )
}
export async function getMetaData(
  store: any,
  data: Req['getMetaData'],
  options?: Parameters<
    typeof metaDataService.endpoints.getMetaData.initiate
  >[1],
) {
  return store.dispatch(
    metaDataService.endpoints.getMetaData.initiate(data, options),
  )
}
export async function getListMetaData(
  store: any,
  data: Req['getListMetaData'],
  options?: Parameters<
    typeof metaDataService.endpoints.getListMetaData.initiate
  >[1],
) {
  return store.dispatch(
    metaDataService.endpoints.getListMetaData.initiate(data, options),
  )
}
export async function updateMetaData(
  store: any,
  data: Req['updateMetaData'],
  options?: Parameters<
    typeof metaDataService.endpoints.updateMetaData.initiate
  >[1],
) {
  return store.dispatch(
    metaDataService.endpoints.updateMetaData.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateMetaDataMutation,
  useDeleteMetaDataMutation,
  useGetListMetaDataQuery,
  useGetMetaDataQuery,
  useUpdateMetaDataMutation,
  // END OF EXPORTS
} = metaDataService

/* Usage examples:
const { data, isLoading } = useGetMetaDataQuery({ id: 2 }, {}) //get hook
const [createMetaData, { isLoading, data, isSuccess }] = useCreateMetaDataMutation() //create hook
metaDataService.endpoints.getMetaData.select({id: 2})(store.getState()) //access data from any function
*/
