import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const accountService = service
  .enhanceEndpoints({ addTagTypes: ['Account'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      deleteAccount: builder.mutation<Res['account'], Req['deleteAccount']>({
        invalidatesTags: [{ id: 'LIST', type: 'Account' }],
        query: (query: Req['deleteAccount']) => ({
          body: {
            current_password: query.current_password,
            delete_orphan_organisations: query.delete_orphan_organisations,
          },
          method: 'DELETE',
          url: `auth/users/me/`,
        }),
      }),
      updateAccount: builder.mutation<Res['account'], Req['updateAccount']>({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'Account' },
          { id: res?.id, type: 'Account' },
        ],
        query: (query: Req['updateAccount']) => ({
          body: query,
          method: 'PUT',
          url: `auth/users/me/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function updateAccount(
  store: any,
  data: Req['updateAccount'],
  options?: Parameters<
    typeof accountService.endpoints.updateAccount.initiate
  >[1],
) {
  store.dispatch(accountService.endpoints.updateAccount.initiate(data, options))
  return Promise.all(
    store.dispatch(accountService.util.getRunningQueriesThunk()),
  )
}

export async function deleteAccount(
  store: any,
  data: Req['deleteAccount'],
  options?: Parameters<
    typeof accountService.endpoints.deleteAccount.initiate
  >[1],
) {
  store.dispatch(accountService.endpoints.deleteAccount.initiate(data, options))
  return Promise.all(
    store.dispatch(accountService.util.getRunningQueriesThunk()),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useDeleteAccountMutation,
  useUpdateAccountMutation,
  // END OF EXPORTS
} = accountService

/* Usage examples:
const { data, isLoading } = useGetAccountQuery({ id: 2 }, {}) //get hook
const [createAccount, { isLoading, data, isSuccess }] = useCreateAccountMutation() //create hook
accountService.endpoints.getAccount.select({id: 2})(store.getState()) //access data from any function
*/
