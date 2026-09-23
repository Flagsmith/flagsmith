import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const scimConfigurationService = service
  .enhanceEndpoints({
    addTagTypes: ['ScimConfiguration'],
  })
  .injectEndpoints({
    endpoints: (builder) => ({
      createScimConfiguration: builder.mutation<
        Res['scimConfigurationWithToken'],
        Req['createScimConfiguration']
      >({
        invalidatesTags: (_res, _err, query) => [
          { id: query.organisation_id, type: 'ScimConfiguration' },
        ],
        query: (query: Req['createScimConfiguration']) => ({
          method: 'POST',
          url: `organisations/${query.organisation_id}/scim/`,
        }),
      }),
      deleteScimConfiguration: builder.mutation<
        void,
        Req['deleteScimConfiguration']
      >({
        invalidatesTags: (_res, _err, query) => [
          { id: query.organisation_id, type: 'ScimConfiguration' },
        ],
        query: (query: Req['deleteScimConfiguration']) => ({
          method: 'DELETE',
          url: `organisations/${query.organisation_id}/scim/`,
        }),
      }),
      getScimConfiguration: builder.query<
        Res['scimConfiguration'],
        Req['getScimConfiguration']
      >({
        providesTags: (_res, _err, query) => [
          { id: query.organisation_id, type: 'ScimConfiguration' },
        ],
        query: (query: Req['getScimConfiguration']) => ({
          url: `organisations/${query.organisation_id}/scim/`,
        }),
      }),
      regenerateScimToken: builder.mutation<
        Res['scimConfigurationWithToken'],
        Req['regenerateScimToken']
      >({
        invalidatesTags: (_res, _err, query) => [
          { id: query.organisation_id, type: 'ScimConfiguration' },
        ],
        query: (query: Req['regenerateScimToken']) => ({
          method: 'POST',
          url: `organisations/${query.organisation_id}/scim/regenerate-token/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createScimConfiguration(
  store: any,
  data: Req['createScimConfiguration'],
  options?: Parameters<
    typeof scimConfigurationService.endpoints.createScimConfiguration.initiate
  >[1],
) {
  return store.dispatch(
    scimConfigurationService.endpoints.createScimConfiguration.initiate(
      data,
      options,
    ),
  )
}
export async function deleteScimConfiguration(
  store: any,
  data: Req['deleteScimConfiguration'],
  options?: Parameters<
    typeof scimConfigurationService.endpoints.deleteScimConfiguration.initiate
  >[1],
) {
  return store.dispatch(
    scimConfigurationService.endpoints.deleteScimConfiguration.initiate(
      data,
      options,
    ),
  )
}
export async function getScimConfiguration(
  store: any,
  data: Req['getScimConfiguration'],
  options?: Parameters<
    typeof scimConfigurationService.endpoints.getScimConfiguration.initiate
  >[1],
) {
  return store.dispatch(
    scimConfigurationService.endpoints.getScimConfiguration.initiate(
      data,
      options,
    ),
  )
}
export async function regenerateScimToken(
  store: any,
  data: Req['regenerateScimToken'],
  options?: Parameters<
    typeof scimConfigurationService.endpoints.regenerateScimToken.initiate
  >[1],
) {
  return store.dispatch(
    scimConfigurationService.endpoints.regenerateScimToken.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateScimConfigurationMutation,
  useDeleteScimConfigurationMutation,
  useGetScimConfigurationQuery,
  useRegenerateScimTokenMutation,
  // END OF EXPORTS
} = scimConfigurationService

/* Usage examples:
const { data, isLoading } = useGetScimConfigurationQuery({ organisation_id: 2 }) //get hook
const [createScimConfiguration, { isLoading, data, isSuccess }] = useCreateScimConfigurationMutation() //create hook
scimConfigurationService.endpoints.getScimConfiguration.select({organisation_id: 2})(store.getState()) //access data from any function
*/
