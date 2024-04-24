import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'

export const githubService = service
  .enhanceEndpoints({ addTagTypes: ['Github'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getGithubIssues: builder.query<
        Res['githubIssues'],
        Req['getGithubIssues']
      >({
        providesTags: [{ id: 'LIST', type: 'Github' }],
        query: (query: Req['getGithubIssues']) => ({
          url: `organisations/${query.organisation_id}/github/issues/?repo_name=${query.repo_name}&repo_owner=${query.repo_owner}`,
        }),
      }),
      getGithubPulls: builder.query<Res['githubPulls'], Req['getGithubPulls']>({
        providesTags: [{ id: 'LIST', type: 'Github' }],
        query: (query: Req['getGithubPulls']) => ({
          url: `organisations/${query.organisation_id}/github/pulls/?repo_name=${query.repo_name}&repo_owner=${query.repo_owner}`,
        }),
      }),
      getGithubRepos: builder.query<Res['githubRepos'], Req['getGithubRepos']>({
        providesTags: [{ id: 'LIST', type: 'Github' }],
        query: (query: Req['getGithubRepos']) => ({
          url: `organisations/${
            query.organisation_id
          }/github/repositories/?${Utils.toParam({
            installation_id: query.installation_id,
          })}`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getGithubIssues(
  store: any,
  data: Req['getGithubIssues'],
  options?: Parameters<
    typeof githubService.endpoints.getGithubIssues.initiate
  >[1],
) {
  return store.dispatch(
    githubService.endpoints.getGithubIssues.initiate(data, options),
  )
}
export async function getGithubPulls(
  store: any,
  data: Req['getGithubPulls'],
  options?: Parameters<
    typeof githubService.endpoints.getGithubPulls.initiate
  >[1],
) {
  return store.dispatch(
    githubService.endpoints.getGithubPulls.initiate(data, options),
  )
}
export async function getGithubRepos(
  store: any,
  data: Req['getGithubRepos'],
  options?: Parameters<
    typeof githubService.endpoints.getGithubRepos.initiate
  >[1],
) {
  return store.dispatch(
    githubService.endpoints.getGithubRepos.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetGithubIssuesQuery,
  useGetGithubPullsQuery,
  useGetGithubReposQuery,
  // END OF EXPORTS
} = githubService

/* Usage examples:
const { data, isLoading } = useGetGithubIssuesQuery({ id: 2 }, {}) //get hook
const [createGithub, { isLoading, data, isSuccess }] = useCreateGithubMutation() //create hook
githubService.endpoints.getGithub.select({id: 2})(store.getState()) //access data from any function
*/
