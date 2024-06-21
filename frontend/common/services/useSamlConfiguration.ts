import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'

export const samlConfigurationService = service
  .enhanceEndpoints({
    addTagTypes: ['SamlConfiguration', 'samlConfigurations'],
  })
  .injectEndpoints({
    endpoints: (builder) => ({
      createSamlConfiguration: builder.mutation<
        Res['samlConfiguration'],
        Req['createSamlConfiguration']
      >({
        invalidatesTags: [
          { id: 'LIST', type: 'SamlConfiguration' },
          { id: 'LIST', type: 'samlConfigurations' },
        ],
        query: (query: Req['createSamlConfiguration']) => ({
          body: query,
          method: 'POST',
          url: `auth/saml/configuration/`,
        }),
      }),
      deleteSamlConfiguration: builder.mutation<
        Res['samlConfiguration'],
        Req['deleteSamlConfiguration']
      >({
        invalidatesTags: [
          { id: 'LIST', type: 'SamlConfiguration' },
          { id: 'LIST', type: 'samlConfigurations' },
        ],
        query: (query: Req['deleteSamlConfiguration']) => ({
          body: query,
          method: 'DELETE',
          url: `auth/saml/configuration/${query.name}/`,
        }),
      }),
      getSamlConfiguration: builder.query<
        Res['samlConfiguration'],
        Req['getSamlConfiguration']
      >({
        providesTags: (res) => [{ id: res?.name, type: 'SamlConfiguration' }],
        query: (query: Req['getSamlConfiguration']) => ({
          url: `auth/saml/configuration/${query.name}/`,
        }),
      }),
      getSamlConfigurationMetadata: builder.query<
        Res['samlMetadata'],
        Req['getSamlConfigurationMetadata']
      >({
        providesTags: (res) => [
          { id: res?.entity_id, type: 'SamlConfiguration' },
        ],
        query: (query: Req['getSamlConfigurationMetadata']) => ({
          headers: { Accept: 'application/xml' },
          url: `auth/saml/${query.name}/metadata/`,
        }),
      }),
      getSamlConfigurations: builder.query<
        Res['samlConfigurations'],
        Req['getSamlConfigurations']
      >({
        providesTags: [{ id: 'LIST', type: 'samlConfigurations' }],
        query: (query: Req['getSamlConfigurations']) => ({
          url: `auth/saml/configuration/?${Utils.toParam({
            organisation: query.organisation_id,
          })}`,
        }),
      }),
      updateSamlConfiguration: builder.mutation<
        Res['samlConfiguration'],
        Req['updateSamlConfiguration']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'SamlConfiguration' },
          { id: 'LIST', type: 'samlConfigurations' },
          { id: res?.name, type: 'SamlConfiguration' },
        ],
        query: (query: Req['updateSamlConfiguration']) => ({
          body: query.body,
          method: 'PUT',
          url: `auth/saml/configuration/${query.name}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createSamlConfiguration(
  store: any,
  data: Req['createSamlConfiguration'],
  options?: Parameters<
    typeof samlConfigurationService.endpoints.createSamlConfiguration.initiate
  >[1],
) {
  return store.dispatch(
    samlConfigurationService.endpoints.createSamlConfiguration.initiate(
      data,
      options,
    ),
  )
}
export async function deleteSamlConfiguration(
  store: any,
  data: Req['deleteSamlConfiguration'],
  options?: Parameters<
    typeof samlConfigurationService.endpoints.deleteSamlConfiguration.initiate
  >[1],
) {
  return store.dispatch(
    samlConfigurationService.endpoints.deleteSamlConfiguration.initiate(
      data,
      options,
    ),
  )
}
export async function getSamlConfiguration(
  store: any,
  data: Req['getSamlConfiguration'],
  options?: Parameters<
    typeof samlConfigurationService.endpoints.getSamlConfiguration.initiate
  >[1],
) {
  return store.dispatch(
    samlConfigurationService.endpoints.getSamlConfiguration.initiate(
      data,
      options,
    ),
  )
}
export async function getSamlConfigurations(
  store: any,
  data: Req['getSamlConfigurations'],
  options?: Parameters<
    typeof samlConfigurationService.endpoints.getSamlConfigurations.initiate
  >[1],
) {
  return store.dispatch(
    samlConfigurationService.endpoints.getSamlConfigurations.initiate(
      data,
      options,
    ),
  )
}
export async function getSamlConfigurationMetadata(
  store: any,
  data: Req['getSamlConfigurationMetadata'],
  options?: Parameters<
    typeof samlConfigurationService.endpoints.getSamlConfigurationMetadata.initiate
  >[1],
) {
  return store.dispatch(
    samlConfigurationService.endpoints.getSamlConfigurationMetadata.initiate(
      data,
      options,
    ),
  )
}
export async function updateSamlConfiguration(
  store: any,
  data: Req['updateSamlConfiguration'],
  options?: Parameters<
    typeof samlConfigurationService.endpoints.updateSamlConfiguration.initiate
  >[1],
) {
  return store.dispatch(
    samlConfigurationService.endpoints.updateSamlConfiguration.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateSamlConfigurationMutation,
  useDeleteSamlConfigurationMutation,
  useGetSamlConfigurationMetadataQuery,
  useGetSamlConfigurationQuery,
  useGetSamlConfigurationsQuery,
  useUpdateSamlConfigurationMutation,
  // END OF EXPORTS
} = samlConfigurationService

/* Usage examples:
const { data, isLoading } = useGetSamlConfigurationQuery({ id: 2 }, {}) //get hook
const [createSamlConfiguration, { isLoading, data, isSuccess }] = useCreateSamlConfigurationMutation() //create hook
samlConfigurationService.endpoints.getSamlConfiguration.select({id: 2})(store.getState()) //access data from any function
*/
