import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const featureExportService = service
  .enhanceEndpoints({ addTagTypes: ['FeatureExport'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createFeatureExport: builder.mutation<
        Res['featureExport'],
        Req['createFeatureExport']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'FeatureExport' }],
        query: (query: Req['createFeatureExport']) => ({
          body: query,
          method: 'POST',
          url: `features/create-feature-export/`,
        }),
      }),
      getFeatureExport: builder.query<
        Res['featureExport'],
        Req['getFeatureExport']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'FeatureExport' }],
        query: (query: Req['getFeatureExport']) => ({
          url: `features/download-feature-export/${query.id}`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createFeatureExport(
  store: any,
  data: Req['createFeatureExport'],
  options?: Parameters<
    typeof featureExportService.endpoints.createFeatureExport.initiate
  >[1],
) {
  store.dispatch(
    featureExportService.endpoints.createFeatureExport.initiate(data, options),
  )
  return Promise.all(
    store.dispatch(featureExportService.util.getRunningQueriesThunk()),
  )
}
export async function getFeatureExport(
  store: any,
  data: Req['getFeatureExport'],
  options?: Parameters<
    typeof featureExportService.endpoints.getFeatureExport.initiate
  >[1],
) {
  store.dispatch(
    featureExportService.endpoints.getFeatureExport.initiate(data, options),
  )
  return Promise.all(
    store.dispatch(featureExportService.util.getRunningQueriesThunk()),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateFeatureExportMutation,
  useGetFeatureExportQuery,
  // END OF EXPORTS
} = featureExportService

/* Usage examples:
const { data, isLoading } = useGetFeatureExportQuery({ id: 2 }, {}) //get hook
const [createFeatureExport, { isLoading, data, isSuccess }] = useCreateFeatureExportMutation() //create hook
featureExportService.endpoints.getFeatureExport.select({id: 2})(store.getState()) //access data from any function
*/
