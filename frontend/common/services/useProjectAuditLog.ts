import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const projectAuditLogService = service
  .enhanceEndpoints({ addTagTypes: ['ProjectAuditLog'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getProjectAuditLogs: builder.query<
        Res['projectAuditLogs'],
        Req['getProjectAuditLogs']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'ProjectAuditLog' }],
        query: (query: Req['getProjectAuditLogs']) => ({
          url: `projects/${query.id}/audit/?${Utils.toParam(query.params)}`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getProjectAuditLogs(
  store: any,
  data: Req['getProjectAuditLogs'],
  options?: Parameters<
    typeof projectAuditLogService.endpoints.getProjectAuditLogs.initiate
  >[1],
) {
  store.dispatch(
    projectAuditLogService.endpoints.getProjectAuditLogs.initiate(
      data,
      options,
    ),
  )
  return Promise.all(
    store.dispatch(projectAuditLogService.util.getRunningQueriesThunk()),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetProjectAuditLogsQuery,
  // END OF EXPORTS
} = projectAuditLogService

/* Usage examples:
const { data, isLoading } = useGetProjectAuditLogsQuery({ id: 2 }, {}) //get hook
const [createProjectAuditLogs, { isLoading, data, isSuccess }] = useCreateProjectAuditLogsMutation() //create hook
projectAuditLogService.endpoints.getProjectAuditLogs.select({id: 2})(store.getState()) //access data from any function
*/
