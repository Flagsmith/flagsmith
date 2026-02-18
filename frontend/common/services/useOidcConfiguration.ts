import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'

export const oidcConfigurationService = service
  .enhanceEndpoints({
    addTagTypes: ['OidcConfiguration', 'oidcConfigurations'],
  })
  .injectEndpoints({
    endpoints: (builder) => ({
      createOidcConfiguration: builder.mutation<
        Res['oidcConfiguration'],
        Req['createOidcConfiguration']
      >({
        invalidatesTags: [
          { id: 'LIST', type: 'OidcConfiguration' },
          { id: 'LIST', type: 'oidcConfigurations' },
        ],
        query: (query: Req['createOidcConfiguration']) => ({
          body: query,
          method: 'POST',
          url: `auth/oauth/oidc/configuration/`,
        }),
      }),
      deleteOidcConfiguration: builder.mutation<
        Res['oidcConfiguration'],
        Req['deleteOidcConfiguration']
      >({
        invalidatesTags: [
          { id: 'LIST', type: 'OidcConfiguration' },
          { id: 'LIST', type: 'oidcConfigurations' },
        ],
        query: (query: Req['deleteOidcConfiguration']) => ({
          method: 'DELETE',
          url: `auth/oauth/oidc/configuration/${query.name}/`,
        }),
      }),
      getOidcConfiguration: builder.query<
        Res['oidcConfiguration'],
        Req['getOidcConfiguration']
      >({
        providesTags: (res) => [{ id: res?.name, type: 'OidcConfiguration' }],
        query: (query: Req['getOidcConfiguration']) => ({
          url: `auth/oauth/oidc/configuration/${query.name}/`,
        }),
      }),
      getOidcConfigurations: builder.query<
        Res['oidcConfigurations'],
        Req['getOidcConfigurations']
      >({
        providesTags: [{ id: 'LIST', type: 'oidcConfigurations' }],
        query: (query: Req['getOidcConfigurations']) => ({
          url: `auth/oauth/oidc/configuration/?${Utils.toParam({
            organisation: query.organisation_id,
          })}`,
        }),
      }),
      updateOidcConfiguration: builder.mutation<
        Res['oidcConfiguration'],
        Req['updateOidcConfiguration']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'OidcConfiguration' },
          { id: 'LIST', type: 'oidcConfigurations' },
          { id: res?.name, type: 'OidcConfiguration' },
        ],
        query: (query: Req['updateOidcConfiguration']) => ({
          body: query.body,
          method: 'PUT',
          url: `auth/oauth/oidc/configuration/${query.name}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createOidcConfiguration(
  store: any,
  data: Req['createOidcConfiguration'],
  options?: Parameters<
    typeof oidcConfigurationService.endpoints.createOidcConfiguration.initiate
  >[1],
) {
  return store.dispatch(
    oidcConfigurationService.endpoints.createOidcConfiguration.initiate(
      data,
      options,
    ),
  )
}
export async function deleteOidcConfiguration(
  store: any,
  data: Req['deleteOidcConfiguration'],
  options?: Parameters<
    typeof oidcConfigurationService.endpoints.deleteOidcConfiguration.initiate
  >[1],
) {
  return store.dispatch(
    oidcConfigurationService.endpoints.deleteOidcConfiguration.initiate(
      data,
      options,
    ),
  )
}
export async function getOidcConfiguration(
  store: any,
  data: Req['getOidcConfiguration'],
  options?: Parameters<
    typeof oidcConfigurationService.endpoints.getOidcConfiguration.initiate
  >[1],
) {
  return store.dispatch(
    oidcConfigurationService.endpoints.getOidcConfiguration.initiate(
      data,
      options,
    ),
  )
}
export async function getOidcConfigurations(
  store: any,
  data: Req['getOidcConfigurations'],
  options?: Parameters<
    typeof oidcConfigurationService.endpoints.getOidcConfigurations.initiate
  >[1],
) {
  return store.dispatch(
    oidcConfigurationService.endpoints.getOidcConfigurations.initiate(
      data,
      options,
    ),
  )
}
export async function updateOidcConfiguration(
  store: any,
  data: Req['updateOidcConfiguration'],
  options?: Parameters<
    typeof oidcConfigurationService.endpoints.updateOidcConfiguration.initiate
  >[1],
) {
  return store.dispatch(
    oidcConfigurationService.endpoints.updateOidcConfiguration.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateOidcConfigurationMutation,
  useDeleteOidcConfigurationMutation,
  useGetOidcConfigurationQuery,
  useGetOidcConfigurationsQuery,
  useUpdateOidcConfigurationMutation,
  // END OF EXPORTS
} = oidcConfigurationService
