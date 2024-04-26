import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const githubRepositoryService = service
  .enhanceEndpoints({ addTagTypes: ['GithubRepository'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createGithubRepository: builder.mutation<
        Res['githubRepository'],
        Req['createGithubRepository']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'GithubRepository' }],
        query: (query: Req['createGithubRepository']) => ({
          body: query.body,
          method: 'POST',
          url: `organisations/${query.organisation_id}/integrations/github/${query.github_id}/repositories/`,
        }),
      }),
      deleteGithubRepository: builder.mutation<
        Res['githubRepository'],
        Req['deleteGithubRepository']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'GithubRepository' }],
        query: (query: Req['deleteGithubRepository']) => ({
          body: query,
          method: 'DELETE',
          url: `organisations/${query.organisation_id}/integrations/github/${query.github_id}/repositories/${query.id}/`,
        }),
      }),
      getGithubRepositories: builder.query<
        Res['githubRepository'],
        Req['getGithubRepositories']
      >({
        providesTags: [{ id: 'LIST', type: 'GithubRepository' }],
        query: (query: Req['getGithubRepositories']) => ({
          url: `organisations/${query.organisation_id}/integrations/github/${query.github_id}/repositories/`,
        }),
      }),
      updateGithubRepository: builder.mutation<
        Res['githubRepository'],
        Req['updateGithubRepository']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'GithubRepository' }],
        query: (query: Req['updateGithubRepository']) => ({
          body: query,
          method: 'PUT',
          url: `organisations/${query.organisation_id}/integrations/github/${query.github_id}/repositories/${query.id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createGithubRepository(
  store: any,
  data: Req['createGithubRepository'],
  options?: Parameters<
    typeof githubRepositoryService.endpoints.createGithubRepository.initiate
  >[1],
) {
  return store.dispatch(
    githubRepositoryService.endpoints.createGithubRepository.initiate(
      data,
      options,
    ),
  )
}
export async function deleteGithubRepository(
  store: any,
  data: Req['deleteGithubRepository'],
  options?: Parameters<
    typeof githubRepositoryService.endpoints.deleteGithubRepository.initiate
  >[1],
) {
  return store.dispatch(
    githubRepositoryService.endpoints.deleteGithubRepository.initiate(
      data,
      options,
    ),
  )
}
export async function getGithubRepositories(
  store: any,
  data: Req['getGithubRepositories'],
  options?: Parameters<
    typeof githubRepositoryService.endpoints.getGithubRepositories.initiate
  >[1],
) {
  return store.dispatch(
    githubRepositoryService.endpoints.getGithubRepositories.initiate(
      data,
      options,
    ),
  )
}
export async function updateGithubRepository(
  store: any,
  data: Req['updateGithubRepository'],
  options?: Parameters<
    typeof githubRepositoryService.endpoints.updateGithubRepository.initiate
  >[1],
) {
  return store.dispatch(
    githubRepositoryService.endpoints.updateGithubRepository.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateGithubRepositoryMutation,
  useDeleteGithubRepositoryMutation,
  useGetGithubRepositoriesQuery,
  useUpdateGithubRepositoryMutation,
  // END OF EXPORTS
} = githubRepositoryService

/* Usage examples:
const { data, isLoading } = useGetGithubRepositoryQuery({ id: 2 }, {}) //get hook
const [createGithubRepository, { isLoading, data, isSuccess }] = useCreateGithubRepositoryMutation() //create hook
githubRepositoryService.endpoints.getGithubRepository.select({id: 2})(store.getState()) //access data from any function
*/
