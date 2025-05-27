import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import { profileService } from './useProfile'
import { getStore } from 'common/store'

export const completedTaskService = service
  .enhanceEndpoints({ addTagTypes: ['CompletedTask'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createCompletedTask: builder.mutation<
        Res['completedTask'],
        Req['createCompletedTask']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'CompletedTask' }],
        query: (query: Req['createCompletedTask']) => ({
          body: query,
          method: 'POST',
          url: `/users/me/tasks`,
        }),
        transformResponse: (res) => {
          getStore().dispatch(profileService.util.invalidateTags(['Profile']))
          return res
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createCompletedTask(
  store: any,
  data: Req['createCompletedTask'],
  options?: Parameters<
    typeof completedTaskService.endpoints.createCompletedTask.initiate
  >[1],
) {
  return store.dispatch(
    completedTaskService.endpoints.createCompletedTask.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateCompletedTaskMutation,
  // END OF EXPORTS
} = completedTaskService

/* Usage examples:
const { data, isLoading } = useGetCompletedTaskQuery({ id: 2 }, {}) //get hook
const [createCompletedTask, { isLoading, data, isSuccess }] = useCreateCompletedTaskMutation() //create hook
completedTaskService.endpoints.getCompletedTask.select({id: 2})(store.getState()) //access data from any function
*/
