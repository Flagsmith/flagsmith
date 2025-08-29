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
        providesTags: ['CodeReferences'],
        query: (query: Req['getFeatureCodeReferences']) => ({
          url: `projects/${query.projectId}/features/${query.featureId}/code-references/`,
        }),
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
