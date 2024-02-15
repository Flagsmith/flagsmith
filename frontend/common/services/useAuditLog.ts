import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'
import transformCorePaging from 'common/transformCorePaging'

export const auditLogService = service
  .enhanceEndpoints({ addTagTypes: ['AuditLog'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getAuditLogs: builder.query<Res['auditLogs'], Req['getAuditLogs']>({
        providesTags: (_, _2, q) => [
          { id: `LIST-${q.project}`, type: 'AuditLog' },
        ],
        query: (params) => {
          if (params.project) {
            const { project, ...rest } = params
            return {
              url: `projects/${project}/audit/?${Utils.toParam({
                ...rest,
              })}`,
            }
          }
          return {
            url: `audit/?${Utils.toParam(params)}`,
          }
        },
        transformResponse: (res, _, req) => transformCorePaging(req, res),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getAuditLogs(
  store: any,
  data: Req['getAuditLogs'],
  options?: Parameters<
    typeof auditLogService.endpoints.getAuditLogs.initiate
  >[1],
) {
  store.dispatch(auditLogService.endpoints.getAuditLogs.initiate(data, options))
  return Promise.all(
    store.dispatch(auditLogService.util.getRunningQueriesThunk()),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetAuditLogsQuery,
  // END OF EXPORTS
} = auditLogService

/* Usage examples:
const { data, isLoading } = useGetAuditLogsQuery({ id: 2 }, {}) //get hook
const [createAuditLogs, { isLoading, data, isSuccess }] = useCreateAuditLogsMutation() //create hook
auditLogService.endpoints.getAuditLogs.select({id: 2})(store.getState()) //access data from any function
*/
