import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const deleteUserAccountService = service
  .enhanceEndpoints({ addTagTypes: ['DeleteUserAccount'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      deleteDeleteUserAccount: builder.mutation<
        Res['deleteUserAccount'],
        Req['deleteDeleteUserAccount']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'DeleteUserAccount' }],
        query: (query: Req['deleteDeleteUserAccount']) => ({
          body: { current_password: query.current_password },
          method: 'DELETE',
          url: `auth/users/${query.id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function deleteDeleteUserAccount(
  store: any,
  data: Req['deleteDeleteUserAccount'],
  options?: Parameters<
    typeof deleteUserAccountService.endpoints.deleteDeleteUserAccount.initiate
  >[1],
) {
  store.dispatch(
    deleteUserAccountService.endpoints.deleteDeleteUserAccount.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(deleteUserAccountService.util.getRunningQueriesThunk()),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useDeleteDeleteUserAccountMutation,
  // END OF EXPORTS
} = deleteUserAccountService

/* Usage examples:
const { data, isLoading } = useGetDeleteUserAccountQuery({ id: 2 }, {}) //get hook
const [createDeleteUserAccount, { isLoading, data, isSuccess }] = useCreateDeleteUserAccountMutation() //create hook
deleteUserAccountService.endpoints.getDeleteUserAccount.select({id: 2})(store.getState()) //access data from any function
*/
