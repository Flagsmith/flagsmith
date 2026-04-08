import { service } from 'common/service'
import { Req } from 'common/types/requests'
import {
  EdgeIdentityOverrideItem,
  FeatureState,
  IdentityOverride,
  PagedResponse,
  Res,
} from 'common/types/responses'
import Utils from 'common/utils/utils'

const identityOverrideService = service
  .enhanceEndpoints({ addTagTypes: ['IdentityOverride'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createIdentityOverride: builder.mutation<
        FeatureState,
        Req['createIdentityOverride']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'IdentityOverride' }],
        query: ({
          enabled,
          environmentId,
          feature_state_value,
          featureId,
          identityId,
        }) => ({
          body: {
            enabled,
            feature: featureId,
            feature_state_value: feature_state_value ?? null,
          },
          method: 'POST',
          url: `environments/${environmentId}/${Utils.getIdentitiesEndpoint()}/${identityId}/${Utils.getFeatureStatesEndpoint()}/`,
        }),
      }),
      getIdentityOverrides: builder.query<
        Res['identityOverrides'],
        Req['getIdentityOverrides']
      >({
        providesTags: [{ id: 'LIST', type: 'IdentityOverride' }],
        query: ({ environmentId, featureId, isEdge, page = 1 }) => ({
          url: isEdge
            ? `environments/${environmentId}/edge-identity-overrides?feature=${featureId}&page=${page}`
            : `environments/${environmentId}/${Utils.getFeatureStatesEndpoint()}/?anyIdentity=1&feature=${featureId}&page=${page}`,
        }),
        transformResponse(
          res:
            | PagedResponse<EdgeIdentityOverrideItem>
            | PagedResponse<FeatureState>,
          _,
          { isEdge },
        ): Res['identityOverrides'] {
          if (isEdge) {
            const edgeRes = res as PagedResponse<EdgeIdentityOverrideItem>
            return {
              ...edgeRes,
              results: edgeRes.results.map((v) => ({
                ...v.feature_state,
                identity: {
                  id: v.identity_uuid,
                  identifier: v.identifier,
                },
              })) as IdentityOverride[],
            }
          }
          return res as PagedResponse<FeatureState>
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export const {
  useCreateIdentityOverrideMutation,
  useGetIdentityOverridesQuery,
  // END OF EXPORTS
} = identityOverrideService
