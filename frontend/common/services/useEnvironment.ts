import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const environmentService = service
  .enhanceEndpoints({ addTagTypes: ['Environment'] })
    .injectEndpoints({
  endpoints: (builder) => ({

    getEnvironments: builder.query<Res['environments'], Req['getEnvironments']>({
      query: (data) => ({
        url: `environments/?project=${data.projectId}`,
      }),
      providesTags:[{ type: 'Environment', id: 'LIST' },],
    }),
    // END OF ENDPOINTS
  }),
 })

export async function getEnvironments(store: any, data: Req['getEnvironments'], options?: Parameters<typeof environmentService.endpoints.getEnvironments.initiate>[1]) {
  store.dispatch(environmentService.endpoints.getEnvironments.initiate(data,options))
  return Promise.all(store.dispatch(environmentService.util.getRunningQueriesThunk()))
}
  // END OF FUNCTION_EXPORTS

export const {
  useGetEnvironmentsQuery,
  // END OF EXPORTS
} = environmentService

/* Usage examples:
const { data, isLoading } = useGetEnvironmentsQuery({ id: 2 }, {}) //get hook
const [createEnvironments, { isLoading, data, isSuccess }] = useCreateEnvironmentsMutation() //create hook
environmentService.endpoints.getEnvironments.select({id: 2})(store.getState()) //access data from any function
*/
