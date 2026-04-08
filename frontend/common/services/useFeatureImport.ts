import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const featureImportService = service
  .enhanceEndpoints({ addTagTypes: ['FeatureImport'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getFeatureImports: builder.query<
        Res['featureImports'],
        Req['getFeatureImports']
      >({
        providesTags: [{ id: 'LIST', type: 'FeatureImport' }],
        query: (query) => ({
          url: `projects/${query.projectId}/feature-imports/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getFeatureImports(
  store: any,
  data: Req['getFeatureImports'],
  options?: Parameters<
    typeof featureImportService.endpoints.getFeatureImports.initiate
  >[1],
) {
  return Promise.all(
    store.dispatch(featureImportService.util.getRunningQueriesThunk()),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetFeatureImportsQuery,
  // END OF EXPORTS
} = featureImportService

/* Usage examples:
const { data, isLoading } = useGetFeatureImportsQuery({ id: 2 }, {}) //get hook
const [createFeatureImports, { isLoading, data, isSuccess }] = useCreateFeatureImportsMutation() //create hook
featureImportService.endpoints.getFeatureImports.select({id: 2})(store.getState()) //access data from any function
*/
