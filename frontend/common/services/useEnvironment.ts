import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const environmentService = service
  .enhanceEndpoints({ addTagTypes: ['Environment'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getEnvironment: builder.query<Res['environment'], Req['getEnvironment']>({
        providesTags: (res) => [{ id: res?.id, type: 'Environment' }],
        query: (query: Req['getEnvironment']) => ({
          url: `environments/${query.id}/`,
        }),
      }),
      getEnvironments: builder.query<
        Res['environments'],
        Req['getEnvironments']
      >({
        providesTags: [{ id: 'LIST', type: 'Environment' }],
        query: (data) => ({
          url: `environments/?project=${data.projectId}`,
        }),
      }),
      updateEnvironment: builder.mutation<
        Res['environment'],
        Req['updateEnvironment']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'Environment' },
          { id: res?.id, type: 'Environment' },
        ],
        query: (query: Req['updateEnvironment']) => ({
          body: query.body,
          method: 'PUT',
          url: `environments/${query.id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getEnvironments(
  store: any,
  data: Req['getEnvironments'],
  options?: Parameters<
    typeof environmentService.endpoints.getEnvironments.initiate
  >[1],
) {
  return store.dispatch(
    environmentService.endpoints.getEnvironments.initiate(data, options),
  )
}
export async function getEnvironment(
  store: any,
  data: Req['getEnvironment'],
  options?: Parameters<
    typeof environmentService.endpoints.getEnvironment.initiate
  >[1],
) {
  return store.dispatch(
    environmentService.endpoints.getEnvironment.initiate(data, options),
  )
}
export async function updateEnvironment(
  store: any,
  data: Req['updateEnvironment'],
  options?: Parameters<
    typeof environmentService.endpoints.updateEnvironment.initiate
  >[1],
) {
  return store.dispatch(
    environmentService.endpoints.updateEnvironment.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetEnvironmentQuery,
  useGetEnvironmentsQuery,
  useUpdateEnvironmentMutation,
  // END OF EXPORTS
} = environmentService

/* Usage examples:
const { data, isLoading } = useGetEnvironmentsQuery({ id: 2 }, {}) //get hook
const [createEnvironments, { isLoading, data, isSuccess }] = useCreateEnvironmentsMutation() //create hook
environmentService.endpoints.getEnvironments.select({id: 2})(store.getState()) //access data from any function
*/
