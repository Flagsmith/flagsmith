import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const myGroupService = service
  .enhanceEndpoints({ addTagTypes: ['MyGroup'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getMyGroups: builder.query<Res['myGroups'], Req['getMyGroups']>({
        providesTags: [{ id: 'LIST', type: 'MyGroup' }],
        query: (q) => ({
          url: `/organisations/${q.orgId}/groups/my-groups`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getMyGroups(
  store: any,
  data: Req['getMyGroups'],
  options?: Parameters<typeof myGroupService.endpoints.getMyGroups.initiate>[1],
) {
  return store.dispatch(
    myGroupService.endpoints.getMyGroups.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetMyGroupsQuery,
  // END OF EXPORTS
} = myGroupService

/* Usage examples:
const { data, isLoading } = useGetMyGroupsQuery({ id: 2 }, {}) //get hook
const [createMyGroups, { isLoading, data, isSuccess }] = useCreateMyGroupsMutation() //create hook
myGroupService.endpoints.getMyGroups.select({id: 2})(store.getState()) //access data from any function
*/
