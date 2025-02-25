import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const buildVersionService = service
  .enhanceEndpoints({ addTagTypes: ['BuildVersion'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getBuildVersion: builder.query<
        Res['buildVersion'],
        Req['getBuildVersion']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'BuildVersion' }],
        query: (query: Req['getBuildVersion']) => ({
          url: `buildVersion/${query.id}`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getBuildVersion(
  store: any,
  data: Req['getBuildVersion'],
  options?: Parameters<
    typeof buildVersionService.endpoints.getBuildVersion.initiate
  >[1],
) {
  return store.dispatch(
    buildVersionService.endpoints.getBuildVersion.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetBuildVersionQuery,
  // END OF EXPORTS
} = buildVersionService

/* Usage examples:
const { data, isLoading } = useGetBuildVersionQuery({ id: 2 }, {}) //get hook
const [createBuildVersion, { isLoading, data, isSuccess }] = useCreateBuildVersionMutation() //create hook
buildVersionService.endpoints.getBuildVersion.select({id: 2})(store.getState()) //access data from any function
*/
