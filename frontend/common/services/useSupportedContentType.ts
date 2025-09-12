import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const supportedContentTypeService = service
  .enhanceEndpoints({ addTagTypes: ['SupportedContentType'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getSupportedContentType: builder.query<
        Res['supportedContentType'],
        Req['getSupportedContentType']
      >({
        providesTags: [{ id: 'LIST', type: 'SupportedContentType' }],
        query: (query: Req['getSupportedContentType']) => ({
          url: `organisations/${query.organisation_id}/metadata-model-fields/supported-content-types/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getSupportedContentType(
  store: any,
  data: Req['getSupportedContentType'],
  options?: Parameters<
    typeof supportedContentTypeService.endpoints.getSupportedContentType.initiate
  >[1],
) {
  return store.dispatch(
    supportedContentTypeService.endpoints.getSupportedContentType.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetSupportedContentTypeQuery,
  // END OF EXPORTS
} = supportedContentTypeService

/* Usage examples:
const { data, isLoading } = useGetSupportedContentTypeQuery({ id: 2 }, {}) //get hook
const [createSupportedContentType, { isLoading, data, isSuccess }] = useCreateSupportedContentTypeMutation() //create hook
supportedContentTypeService.endpoints.getSupportedContentType.select({id: 2})(store.getState()) //access data from any function
*/
