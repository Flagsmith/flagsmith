import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'

export const githubService = service
  .enhanceEndpoints({ addTagTypes: ['Github'] })
  .injectEndpoints({
    endpoints: (builder) => ({
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
      getGithubResources: builder.query<
        Res['githubResources'],
        Req['getGithubResources']
      >({
        providesTags: [{ id: 'LIST', type: 'Github' }],
        query: (query: Req['getGithubResources']) => ({
          url:
            `organisations/${query.organisation_id}/github/${query.github_resource}/` +
            `?repo_name=${query.repo_name}&repo_owner=${query.repo_owner}&page_size=${query.page_size}&page=${query.page}&search_text=${query.q}`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getGithubResources(
  store: any,
  data: Req['getGithubResources'],
  options?: Parameters<
    typeof githubService.endpoints.getGithubResources.initiate
  >[1],
) {
  return store.dispatch(
    githubService.endpoints.getGithubResources.initiate(data, options),
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
  useGetGithubReposQuery,
  useGetGithubResourcesQuery,
  // END OF EXPORTS
} = githubService

/* Usage examples:
const { data, isLoading } = useGetGithubResourcesQuery({ id: 2 }, {}) //get hook
const [createGithub, { isLoading, data, isSuccess }] = useCreateGithubMutation() //create hook
githubService.endpoints.getGithub.select({id: 2})(store.getState()) //access data from any function
*/
