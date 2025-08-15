import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const codeReferencesService = service
  .enhanceEndpoints({ addTagTypes: ['CodeReferences'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getFeatureCodeReferences: builder.query<
        Res['featureCodeReferences'],
        Req['getFeatureCodeReferences']
      >({
        // query: (query: Req['getFeatureCodeReferences']) => ({
        //   url: `projects/${query.projectId}/features/${query.featureId}/code-references/`,
        // }),
        queryFn: async (query: Req['getFeatureCodeReferences']) => {
          return {
            data: {
              code_references: [
                {
                  file_path: 'flagsmith/api/integrations/slack/views.py',
                  line_number: 35,
                  permalink:
                    'https://github.com/Flagsmith/flagsmith/pull/5931/files#diff-eeac2c6b2db177cd1efd1b93be145042550c8743b0f993e1d4581061ebdd5797R8-R46',
                  repository_url: 'https://github.com/Flagsmith/flagsmith',
                  revision: 'main',
                  scanned_at: '2021-01-01',
                  vcs_provider: 'github',
                },
                {
                  file_path: 'flagsmith/api/organisations/invites/models.py',
                  line_number: 12,
                  permalink:
                    'https://github.com/Flagsmith/flagsmith/pull/5931/files#diff-eeac2c6b2db177cd1efd1b93be145042550c8743b0f993e1d4581061ebdd5797R8-R46',
                  repository_url: 'https://github.com/Flagsmith/flagsmith',
                  revision: 'main',
                  scanned_at: '2021-01-01',
                  vcs_provider: 'github',
                },
                {
                  file_path: 'flagsmith/analytics.py',
                  line_number: 17,
                  permalink:
                    'https://github.com/Flagsmith/flagsmith-python-client/blob/main/flagsmith/analytics.py#L17',
                  repository_url:
                    'https://github.com/Flagsmith/flagsmith-python-client',
                  revision: 'main',
                  scanned_at: '2021-01-01',
                  vcs_provider: 'gitlab',
                },
              ],
              first_scanned_at: '2021-01-01',
              last_scanned_at: '2021-01-01',
            },
          }
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export const {
  useGetFeatureCodeReferencesQuery,
  // END OF EXPORTS
} = codeReferencesService

/* Usage examples:
const { data, isLoading } = useGetAccountQuery({ id: 2 }, {}) //get hook
const [createAccount, { isLoading, data, isSuccess }] = useCreateAccountMutation() //create hook
accountService.endpoints.getAccount.select({id: 2})(store.getState()) //access data from any function
*/
