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
            data: [
              {
                'code_references': [
                  {
                    'file_path': 'src/components/Button.js',
                    'line_number': 42,
                    'permalink':
                      'https://github.com/org/repo/blob/abcd123/src/components/Button.js#L42',
                    'vcs_revision': 'abcd123',
                  },
                  {
                    'file_path': 'src/utils/helpers.js',
                    'line_number': 88,
                    'permalink':
                      'https://github.com/Flagsmith/flagsmith/pull/5931/files#diff-eeac2c6b2db177cd1efd1b93be145042550c8743b0f993e1d4581061ebdd5797R8-R46',
                    'vcs_revision': 'abcd123',
                  },
                ],
                'last_feature_found_at': '2025-08-18T14:33:00Z',
                'last_successful_repository_scanned_at': '2025-08-18T14:32:00Z',
                'repository_url': 'https://github.com/flagsmith/flagsmith',
                'vcs_provider': 'github',
              },
              {
                'code_references': [
                  {
                    'file_path': 'flagsmith/analytics.py',
                    'line_number': 17,
                    'permalink':
                      'https://github.com/Flagsmith/flagsmith/pull/5931/files#diff-eeac2c6b2db177cd1efd1b93be145042550c8743b0f993e1d4581061ebdd5797R8-R46',
                    'vcs_revision': 'main',
                  },
                  {
                    file_path: 'flagsmith/api/jwt_cookie/authentication.py',
                    'line_number': 88,
                    'permalink':
                      'https://github.com/Flagsmith/flagsmith/pull/5931/files#diff-eeac2c6b2db177cd1efd1b93be145042550c8743b0f993e1d4581061ebdd5797R8-R46',
                    'vcs_revision': 'abcd123',
                  },
                ],
                'last_feature_found_at': '2025-07-18T14:33:00Z',
                'last_successful_repository_scanned_at': '2025-08-18T14:32:00Z',
                'repository_url':
                  'https://github.com/flagsmith/flagsmith-python-client',
                'vcs_provider': 'github',
              },
            ],
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
