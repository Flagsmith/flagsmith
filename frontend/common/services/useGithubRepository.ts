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
          url: `organisations/${query.organisation_pk}/integrations/github/${query.github_pk}/repositories/`,
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
          url: `organisations/${query.organisation_pk}/integrations/github/${query.github_pk}/repositories/${query.id}/`,
        }),
      }),
      getGithubRepository: builder.query<
        Res['githubRepository'],
        Req['getGithubRepository']
      >({
        providesTags: (res) => [{ id: res?.id, type: 'GithubRepository' }],
        query: (query: Req['getGithubRepository']) => ({
          url: `organisations/${query.organisation_pk}/integrations/github/${query.github_pk}/repositories/${query.id}/`,
        }),
      }),
      updateGithubRepository: builder.mutation<
        Res['githubRepository'],
        Req['updateGithubRepository']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'GithubRepository' },
          { id: res?.id, type: 'GithubRepository' },
        ],
        query: (query: Req['updateGithubRepository']) => ({
          body: query,
          method: 'PUT',
          url: `organisations/${query.organisation_pk}/integrations/github/${query.github_pk}/repositories/${query.id}/`,
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
export async function getGithubRepository(
  store: any,
  data: Req['getGithubRepository'],
  options?: Parameters<
    typeof githubRepositoryService.endpoints.getGithubRepository.initiate
  >[1],
) {
  return store.dispatch(
    githubRepositoryService.endpoints.getGithubRepository.initiate(
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
  useGetGithubRepositoryQuery,
  useUpdateGithubRepositoryMutation,
  // END OF EXPORTS
} = githubRepositoryService

/* Usage examples:
const { data, isLoading } = useGetGithubRepositoryQuery({ id: 2 }, {}) //get hook
const [createGithubRepository, { isLoading, data, isSuccess }] = useCreateGithubRepositoryMutation() //create hook
githubRepositoryService.endpoints.getGithubRepository.select({id: 2})(store.getState()) //access data from any function
*/
