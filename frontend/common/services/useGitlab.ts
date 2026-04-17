import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'

export const gitlabService = service
  .enhanceEndpoints({ addTagTypes: ['GitLab'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getGitLabIssues: builder.query<
        Res['gitlabIssues'],
        Req['getGitLabIssues']
      >({
        providesTags: [{ id: 'LIST', type: 'GitLab' }],
        query: (query: Req['getGitLabIssues']) => ({
          url: `projects/${query.project_id}/gitlab/issues/?${Utils.toParam({
            gitlab_project_id: query.gitlab_project_id,
            page: query.page ?? 1,
            page_size: query.page_size ?? 100,
            search_text: query.q || undefined,
            state: 'opened', // Only open items are linkable to feature flags.
          })}`,
        }),
      }),
      getGitLabMergeRequests: builder.query<
        Res['gitlabMergeRequests'],
        Req['getGitLabMergeRequests']
      >({
        providesTags: [{ id: 'LIST', type: 'GitLab' }],
        query: (query: Req['getGitLabMergeRequests']) => ({
          url: `projects/${
            query.project_id
          }/gitlab/merge-requests/?${Utils.toParam({
            gitlab_project_id: query.gitlab_project_id,
            page: query.page ?? 1,
            page_size: query.page_size ?? 100,
            search_text: query.q || undefined,
            state: 'opened', // Only open items are linkable to feature flags.
          })}`,
        }),
      }),
      getGitLabProjects: builder.query<
        Res['gitlabProjects'],
        Req['getGitLabProjects']
      >({
        providesTags: [{ id: 'LIST', type: 'GitLab' }],
        query: (query: Req['getGitLabProjects']) => ({
          url: `projects/${query.project_id}/gitlab/projects/?${Utils.toParam({
            page: query.page ?? 1,
            page_size: query.page_size ?? 100,
          })}`,
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
  useGetGitLabIssuesQuery,
  useGetGitLabMergeRequestsQuery,
  useGetGitLabProjectsQuery,
  // END OF EXPORTS
} = gitlabService
