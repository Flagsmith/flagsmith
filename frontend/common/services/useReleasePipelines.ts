// TODO: Add types
// import { Res } from 'common/types/responses'
// import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const releasePipelinesService = service
  .enhanceEndpoints({ addTagTypes: ['ReleasePipelines'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      // Res['releasePipelines'], Req['getReleasePipelines']
      getReleasePipelines: builder.query<any, any>({
        providesTags: [{ id: 'LIST', type: 'ReleasePipelines' }],
        queryFn: async (query, api, extraOptions, baseQuery) => {
          await new Promise((resolve) => {
            setTimeout(() => {
              resolve({
                data: {
                  results: [],
                },
              })
            }, 1500)
          })

          return {
            data: {
              results: [],
            },
          }
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getReleasePipelines(
  store: any,
  // data: Req['getReleasePipelines'],
  data: any,
  options?: Parameters<
    typeof releasePipelinesService.endpoints.getReleasePipelines.initiate
  >[1],
) {
  return store.dispatch(
    releasePipelinesService.endpoints.getReleasePipelines.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetReleasePipelinesQuery,
  // END OF EXPORTS
} = releasePipelinesService

/* Usage examples:
const { data, isLoading } = useGetReleasePipelinesQuery({ id: 2 }, {}) //get hook
const [createReleasePipelines, { isLoading, data, isSuccess }] = useCreateReleasePipelinesMutation() //create hook
releasePipelinesService.endpoints.getReleasePipelines.select({id: 2})(store.getState()) //access data from any function
*/
