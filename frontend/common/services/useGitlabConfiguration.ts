import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const gitlabConfigurationService = service
  .enhanceEndpoints({ addTagTypes: ['GitLabConfiguration'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getGitLabConfiguration: builder.query<
        Res['gitlabConfiguration'],
        Req['getGitLabConfiguration']
      >({
        providesTags: [{ id: 'LIST', type: 'GitLabConfiguration' }],
        query: (query: Req['getGitLabConfiguration']) => ({
          url: `projects/${query.project_id}/integrations/gitlab/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getGitLabConfiguration(
  store: any,
  data: Req['getGitLabConfiguration'],
  options?: Parameters<
    typeof gitlabConfigurationService.endpoints.getGitLabConfiguration.initiate
  >[1],
) {
  return store.dispatch(
    gitlabConfigurationService.endpoints.getGitLabConfiguration.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetGitLabConfigurationQuery,
  // END OF EXPORTS
} = gitlabConfigurationService

/* Usage examples:
const { data, isLoading } = useGetGitLabConfigurationQuery({ project_id: 2 }, {}) //get hook
gitlabConfigurationService.endpoints.getGitLabConfiguration.select({project_id: 2})(store.getState()) //access data from any function
*/
