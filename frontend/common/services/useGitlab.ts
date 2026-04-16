import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const gitlabService = service
  .enhanceEndpoints({ addTagTypes: ['GitLab'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getGitLabProjects: builder.query<
        Res['gitlabProjects'],
        Req['getGitLabProjects']
      >({
        providesTags: [{ id: 'LIST', type: 'GitLab' }],
        query: (query: Req['getGitLabProjects']) => ({
          url: `projects/${query.project_id}/gitlab/projects/?page_size=${query.page_size ?? 100}&page=${query.page ?? 1}`,
        }),
      }),
      getGitLabIssues: builder.query<
        Res['gitlabIssues'],
        Req['getGitLabIssues']
      >({
        providesTags: [{ id: 'LIST', type: 'GitLab' }],
        query: (query: Req['getGitLabIssues']) => ({
          url:
            `projects/${query.project_id}/gitlab/issues/` +
            `?gitlab_project_id=${query.gitlab_project_id}&page_size=${query.page_size ?? 100}&page=${query.page ?? 1}&search_text=${query.q || ''}&state=opened`,
        }),
      }),
      getGitLabMergeRequests: builder.query<
        Res['gitlabMergeRequests'],
        Req['getGitLabMergeRequests']
      >({
        providesTags: [{ id: 'LIST', type: 'GitLab' }],
        query: (query: Req['getGitLabMergeRequests']) => ({
          url:
            `projects/${query.project_id}/gitlab/merge-requests/` +
            `?gitlab_project_id=${query.gitlab_project_id}&page_size=${query.page_size ?? 100}&page=${query.page ?? 1}&search_text=${query.q || ''}&state=opened`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getGitLabProjects(
  store: any,
  data: Req['getGitLabProjects'],
  options?: Parameters<
    typeof gitlabService.endpoints.getGitLabProjects.initiate
  >[1],
) {
  return store.dispatch(
    gitlabService.endpoints.getGitLabProjects.initiate(data, options),
  )
}
export async function getGitLabIssues(
  store: any,
  data: Req['getGitLabIssues'],
  options?: Parameters<
    typeof gitlabService.endpoints.getGitLabIssues.initiate
  >[1],
) {
  return store.dispatch(
    gitlabService.endpoints.getGitLabIssues.initiate(data, options),
  )
}
export async function getGitLabMergeRequests(
  store: any,
  data: Req['getGitLabMergeRequests'],
  options?: Parameters<
    typeof gitlabService.endpoints.getGitLabMergeRequests.initiate
  >[1],
) {
  return store.dispatch(
    gitlabService.endpoints.getGitLabMergeRequests.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetGitLabProjectsQuery,
  useGetGitLabIssuesQuery,
  useGetGitLabMergeRequestsQuery,
  // END OF EXPORTS
} = gitlabService
