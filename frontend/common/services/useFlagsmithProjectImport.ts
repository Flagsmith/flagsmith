import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import toFormData from 'common/utils/toFormData'

export const flagsmithProjectImportService = service
  .enhanceEndpoints({ addTagTypes: ['FlagsmithProjectImport'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createFlagsmithProjectImport: builder.mutation<
        Res['flagsmithProjectImport'],
        Req['createFlagsmithProjectImport']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'FlagsmithProjectImport' }],
        queryFn: async (query, baseQueryApi, extraOptions, baseQuery) => {
          const { environment_id, ...rest } = query
          const formData = toFormData({ ...rest })

          const { data, error } = await baseQuery({
            body: formData,
            method: 'POST',
            url: `features/feature-import/${environment_id}`,
          })
          return { data, error }
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createFlagsmithProjectImport(
  store: any,
  data: Req['createFlagsmithProjectImport'],
  options?: Parameters<
    typeof flagsmithProjectImportService.endpoints.createFlagsmithProjectImport.initiate
  >[1],
) {
  store.dispatch(
    flagsmithProjectImportService.endpoints.createFlagsmithProjectImport.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(flagsmithProjectImportService.util.getRunningQueriesThunk()),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateFlagsmithProjectImportMutation,
  // END OF EXPORTS
} = flagsmithProjectImportService

/* Usage examples:
const { data, isLoading } = useGetFlagsmithProjectImportQuery({ id: 2 }, {}) //get hook
const [createFlagsmithProjectImport, { isLoading, data, isSuccess }] = useCreateFlagsmithProjectImportMutation() //create hook
flagsmithProjectImportService.endpoints.getFlagsmithProjectImport.select({id: 2})(store.getState()) //access data from any function
*/
