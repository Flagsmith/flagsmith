import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const userService = service
  .enhanceEndpoints({ addTagTypes: ['User'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getUsers: builder.query<Res['users'], Req['getUsers']>({
        providesTags: [{ id: 'LIST', type: 'User' }],
        query: (query) => ({
          url: `organisations/${query.organisationId}/users/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getUsers(
  store: any,
  data: Req['getUsers'],
  options?: Parameters<typeof userService.endpoints.getUsers.initiate>[1],
) {
  return store.dispatch(userService.endpoints.getUsers.initiate(data, options))
}
// END OF FUNCTION_EXPORTS

export const {
  useGetUsersQuery,
  // END OF EXPORTS
} = userService

/* Usage examples:
const { data, isLoading } = useGetUsersQuery({ id: 2 }, {}) //get hook
const [createUsers, { isLoading, data, isSuccess }] = useCreateUsersMutation() //create hook
userService.endpoints.getUsers.select({id: 2})(store.getState()) //access data from any function
*/
