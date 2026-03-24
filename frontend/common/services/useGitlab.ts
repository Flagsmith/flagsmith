import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'

export const gitlabService = service
  .enhanceEndpoints({ addTagTypes: ['Gitlab'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getGitlabProjects: builder.query<
        Res['gitlabProjects'],
        Req['getGitlabProjects']
      >({
        providesTags: [{ id: 'LIST', type: 'Gitlab' }],
        query: (query: Req['getGitlabProjects']) => ({
          url: `projects/${query.project_id}/gitlab/projects/`,
        }),
      }),
      getGitlabResources: builder.query<
        Res['gitlabResources'],
        Req['getGitlabResources']
      >({
        providesTags: [{ id: 'LIST', type: 'Gitlab' }],
        query: (query: Req['getGitlabResources']) => ({
          url:
            `projects/${query.project_id}/gitlab/${query.gitlab_resource}/` +
            `?${Utils.toParam({
              gitlab_project_id: query.gitlab_project_id,
              page: query.page,
              page_size: query.page_size,
              project_name: query.project_name,
            })}`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getGitlabResources(
  store: any,
  data: Req['getGitlabResources'],
  options?: Parameters<
    typeof gitlabService.endpoints.getGitlabResources.initiate
  >[1],
) {
  return store.dispatch(
    gitlabService.endpoints.getGitlabResources.initiate(data, options),
  )
}
export async function getGitlabProjects(
  store: any,
  data: Req['getGitlabProjects'],
  options?: Parameters<
    typeof gitlabService.endpoints.getGitlabProjects.initiate
  >[1],
) {
  return store.dispatch(
    gitlabService.endpoints.getGitlabProjects.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetGitlabProjectsQuery,
  useGetGitlabResourcesQuery,
  // END OF EXPORTS
} = gitlabService

/* Usage examples:
const { data, isLoading } = useGetGitlabResourcesQuery({ project_id: 2, gitlab_resource: 'issues', gitlab_project_id: 1, project_name: 'my-project' }, {}) //get hook
const { data, isLoading } = useGetGitlabProjectsQuery({ project_id: 2 }, {}) //get hook
gitlabService.endpoints.getGitlabProjects.select({ project_id: 2 })(store.getState()) //access data from any function
*/
