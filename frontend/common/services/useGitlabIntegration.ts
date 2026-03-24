import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const gitlabIntegrationService = service
  .enhanceEndpoints({ addTagTypes: ['GitlabIntegration'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createGitlabIntegration: builder.mutation<
        Res['gitlabIntegrations'],
        Req['createGitlabIntegration']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'GitlabIntegration' }],
        query: (query: Req['createGitlabIntegration']) => ({
          body: query.body,
          method: 'POST',
          url: `projects/${query.project_id}/integrations/gitlab/`,
        }),
      }),
      deleteGitlabIntegration: builder.mutation<
        Res['gitlabIntegrations'],
        Req['deleteGitlabIntegration']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'GitlabIntegration' }],
        query: (query: Req['deleteGitlabIntegration']) => ({
          method: 'DELETE',
          url: `projects/${query.project_id}/integrations/gitlab/${query.gitlab_integration_id}/`,
        }),
      }),
      getGitlabIntegration: builder.query<
        Res['gitlabIntegrations'],
        Req['getGitlabIntegration']
      >({
        providesTags: [{ id: 'LIST', type: 'GitlabIntegration' }],
        query: (query: Req['getGitlabIntegration']) => ({
          url: `projects/${query.project_id}/integrations/gitlab/`,
        }),
      }),
      updateGitlabIntegration: builder.mutation<
        Res['gitlabIntegrations'],
        Req['updateGitlabIntegration']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'GitlabIntegration' }],
        query: (query: Req['updateGitlabIntegration']) => ({
          body: query.body,
          method: 'PATCH',
          url: `projects/${query.project_id}/integrations/gitlab/${query.gitlab_integration_id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createGitlabIntegration(
  store: any,
  data: Req['createGitlabIntegration'],
  options?: Parameters<
    typeof gitlabIntegrationService.endpoints.createGitlabIntegration.initiate
  >[1],
) {
  return store.dispatch(
    gitlabIntegrationService.endpoints.createGitlabIntegration.initiate(
      data,
      options,
    ),
  )
}
export async function deleteGitlabIntegration(
  store: any,
  data: Req['deleteGitlabIntegration'],
  options?: Parameters<
    typeof gitlabIntegrationService.endpoints.deleteGitlabIntegration.initiate
  >[1],
) {
  return store.dispatch(
    gitlabIntegrationService.endpoints.deleteGitlabIntegration.initiate(
      data,
      options,
    ),
  )
}
export async function getGitlabIntegration(
  store: any,
  data: Req['getGitlabIntegration'],
  options?: Parameters<
    typeof gitlabIntegrationService.endpoints.getGitlabIntegration.initiate
  >[1],
) {
  return store.dispatch(
    gitlabIntegrationService.endpoints.getGitlabIntegration.initiate(
      data,
      options,
    ),
  )
}
export async function updateGitlabIntegration(
  store: any,
  data: Req['updateGitlabIntegration'],
  options?: Parameters<
    typeof gitlabIntegrationService.endpoints.updateGitlabIntegration.initiate
  >[1],
) {
  return store.dispatch(
    gitlabIntegrationService.endpoints.updateGitlabIntegration.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateGitlabIntegrationMutation,
  useDeleteGitlabIntegrationMutation,
  useGetGitlabIntegrationQuery,
  useUpdateGitlabIntegrationMutation,
  // END OF EXPORTS
} = gitlabIntegrationService

/* Usage examples:
const { data, isLoading } = useGetGitlabIntegrationQuery({ project_id: 2 }, {}) //get hook
const [createGitlabIntegration, { isLoading, data, isSuccess }] = useCreateGitlabIntegrationMutation() //create hook
gitlabIntegrationService.endpoints.getGitlabIntegration.select({ project_id: 2 })(store.getState()) //access data from any function
*/
