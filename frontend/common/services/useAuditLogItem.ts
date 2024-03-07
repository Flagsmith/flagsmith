import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const auditLogItemService = service
  .enhanceEndpoints({ addTagTypes: ['AuditLogItem'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getAuditLogItem: builder.query<
        Res['auditLogItem'],
        Req['getAuditLogItem']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'AuditLogItem' }],
        query: (query: Req['getAuditLogItem']) => ({
          url: `projects/${query.projectId}/audit/${query.id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getAuditLogItem(
  store: any,
  data: Req['getAuditLogItem'],
  options?: Parameters<
    typeof auditLogItemService.endpoints.getAuditLogItem.initiate
  >[1],
) {
  return store.dispatch(
    auditLogItemService.endpoints.getAuditLogItem.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetAuditLogItemQuery,
  // END OF EXPORTS
} = auditLogItemService

/* Usage examples:
const { data, isLoading } = useGetAuditLogItemQuery({ id: 2 }, {}) //get hook
const [createAuditLogItem, { isLoading, data, isSuccess }] = useCreateAuditLogItemMutation() //create hook
auditLogItemService.endpoints.getAuditLogItem.select({id: 2})(store.getState()) //access data from any function
*/
