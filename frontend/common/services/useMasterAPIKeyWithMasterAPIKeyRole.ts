import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const masterAPIKeyWithMasterAPIKeyRoleService = service
  .enhanceEndpoints({ addTagTypes: ['MasterAPIKeyWithMasterAPIKeyRole'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getMasterAPIKeyWithMasterAPIKeyRoles: builder.query<
        Res['masterAPIKeyWithMasterAPIKeyRoles'],
        Req['getMasterAPIKeyWithMasterAPIKeyRoles']
      >({
        providesTags: (res) => [
          { id: res?.id, type: 'MasterAPIKeyWithMasterAPIKeyRole' },
        ],
        query: (query: Req['getMasterAPIKeyWithMasterAPIKeyRoles']) => ({
          url: `organisations/${query.org_id}/master-api-key-roles/${query.prefix}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getMasterAPIKeyWithMasterAPIKeyRoles(
  store: any,
  data: Req['getMasterAPIKeyWithMasterAPIKeyRoles'],
  options?: Parameters<
    typeof masterAPIKeyWithMasterAPIKeyRoleService.endpoints.getMasterAPIKeyWithMasterAPIKeyRoles.initiate
  >[1],
) {
  return store.dispatch(
    masterAPIKeyWithMasterAPIKeyRoleService.endpoints.getMasterAPIKeyWithMasterAPIKeyRoles.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetMasterAPIKeyWithMasterAPIKeyRolesQuery,
  // END OF EXPORTS
} = masterAPIKeyWithMasterAPIKeyRoleService

/* Usage examples:
const { data, isLoading } = useGetMasterAPIKeyWithMasterAPIKeyRolesQuery({ id: 2 }, {}) //get hook
const [createMasterAPIKeyWithMasterAPIKeyRoles, { isLoading, data, isSuccess }] = useCreateMasterAPIKeyWithMasterAPIKeyRolesMutation() //create hook
masterAPIKeyWithMasterAPIKeyRoleService.endpoints.getMasterAPIKeyWithMasterAPIKeyRoles.select({id: 2})(store.getState()) //access data from any function
*/
