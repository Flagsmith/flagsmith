import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const userEmailService = service
  .enhanceEndpoints({ addTagTypes: ['UserEmail'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      updateUserEmail: builder.mutation<
        Res['userEmail'],
        Req['updateUserEmail']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'UserEmail' },
          { id: res?.id, type: 'UserEmail' },
        ],
        query: (query: Req['updateUserEmail']) => ({
          body: query,
          method: 'POST',
          url: `auth/users/set_email/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function updateUserEmail(
  store: any,
  data: Req['updateUserEmail'],
  options?: Parameters<
    typeof userEmailService.endpoints.updateUserEmail.initiate
  >[1],
) {
  store.dispatch(
    userEmailService.endpoints.updateUserEmail.initiate(data, options),
  )
  return Promise.all(
    store.dispatch(userEmailService.util.getRunningQueriesThunk()),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useUpdateUserEmailMutation,
  // END OF EXPORTS
} = userEmailService

/* Usage examples:
const { data, isLoading } = useGetUserEmailQuery({ id: 2 }, {}) //get hook
const [createUserEmail, { isLoading, data, isSuccess }] = useCreateUserEmailMutation() //create hook
userEmailService.endpoints.getUserEmail.select({id: 2})(store.getState()) //access data from any function
*/
