import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const githubIntegrationService = service
  .enhanceEndpoints({ addTagTypes: ['GithubIntegration'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createGithubIntegration: builder.mutation<
        Res['githubIntegrations'],
        Req['createGithubIntegration']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'GithubIntegration' }],
        query: (query: Req['createGithubIntegration']) => ({
          body: query.body,
          method: 'POST',
          url: `organisations/${query.organisation_id}/integrations/github/`,
        }),
      }),
      deleteGithubIntegration: builder.mutation<
        Res['githubIntegrations'],
        Req['deleteGithubIntegration']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'GithubIntegration' }],
        query: (query: Req['deleteGithubIntegration']) => ({
          method: 'DELETE',
          url: `organisations/${query.organisation_id}/integrations/github/${query.github_integration_id}/`,
        }),
      }),
      getGithubIntegration: builder.query<
        Res['githubIntegrations'],
        Req['getGithubIntegration']
      >({
        providesTags: [{ id: 'LIST', type: 'GithubIntegration' }],
        query: (query: Req['getGithubIntegration']) => ({
          url: `organisations/${query.organisation_id}/integrations/github/`,
        }),
      }),
      updateGithubIntegration: builder.mutation<
        Res['githubIntegrations'],
        Req['updateGithubIntegration']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'GithubIntegration' }],
        query: (query: Req['updateGithubIntegration']) => ({
          body: query,
          method: 'PUT',
          url: `organisations/${query.organisation_id}/integrations/github/${query.github_integration_id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createGithubIntegration(
  store: any,
  data: Req['createGithubIntegration'],
  options?: Parameters<
    typeof githubIntegrationService.endpoints.createGithubIntegration.initiate
  >[1],
) {
  return store.dispatch(
    githubIntegrationService.endpoints.createGithubIntegration.initiate(
      data,
      options,
    ),
  )
}
export async function deleteGithubIntegration(
  store: any,
  data: Req['deleteGithubIntegration'],
  options?: Parameters<
    typeof githubIntegrationService.endpoints.deleteGithubIntegration.initiate
  >[1],
) {
  return store.dispatch(
    githubIntegrationService.endpoints.deleteGithubIntegration.initiate(
      data,
      options,
    ),
  )
}
export async function getGithubIntegration(
  store: any,
  data: Req['getGithubIntegration'],
  options?: Parameters<
    typeof githubIntegrationService.endpoints.getGithubIntegration.initiate
  >[1],
) {
  return store.dispatch(
    githubIntegrationService.endpoints.getGithubIntegration.initiate(
      data,
      options,
    ),
  )
}
export async function updateGithubIntegration(
  store: any,
  data: Req['updateGithubIntegration'],
  options?: Parameters<
    typeof githubIntegrationService.endpoints.updateGithubIntegration.initiate
  >[1],
) {
  return store.dispatch(
    githubIntegrationService.endpoints.updateGithubIntegration.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateGithubIntegrationMutation,
  useDeleteGithubIntegrationMutation,
  useGetGithubIntegrationQuery,
  useUpdateGithubIntegrationMutation,
  // END OF EXPORTS
} = githubIntegrationService

/* Usage examples:
const { data, isLoading } = useGetGithubIntegrationQuery({ id: 2 }, {}) //get hook
const [createGithubIntegration, { isLoading, data, isSuccess }] = useCreateGithubIntegrationMutation() //create hook
githubIntegrationService.endpoints.getGithubIntegration.select({id: 2})(store.getState()) //access data from any function
*/
