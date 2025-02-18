import { IdentityTrait, Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import Utils from 'common/utils/utils'

function getTraitEndpoint(
  use_edge_identities: boolean,
  environmentId: string,
  userId: string,
) {
  if (use_edge_identities) {
    return `/environments/${environmentId}/edge-identities/${userId}/list-traits/`
  }
  return `/environments/${environmentId}/identities/${userId}/traits/`
}

function getUpdateTraitEndpoint(
  use_edge_identities: boolean,
  environmentId: string,
  userId: string,
  id?: number,
) {
  if (use_edge_identities) {
    return `/environments/${environmentId}/edge-identities/${userId}/update-traits/`
  }
  return `/environments/${environmentId}/identities/${userId}/traits/${
    id ? `${id}/` : ''
  }`
}

function getTraitBody(
  use_edge_identities: boolean,
  identity: string,
  trait: IdentityTrait,
) {
  const { trait_key, trait_value } = trait
  return {
    identity: !use_edge_identities ? { identifier: identity } : undefined,
    trait_key,
    ...(use_edge_identities
      ? { trait_value }
      : Utils.valueToTrait(trait_value)),
  }
}
export const identityTraitService = service
  .enhanceEndpoints({ addTagTypes: ['IdentityTrait'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createIdentityTrait: builder.mutation<
        Res['identityTrait'],
        Req['createIdentityTrait']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'IdentityTrait' }],
        query: (query: Req['createIdentityTrait']) => {
          return {
            body: getTraitBody(
              query.use_edge_identities,
              query.identity,
              query.data,
            ),
            method: query.use_edge_identities ? 'PUT' : 'POST',
            url: getUpdateTraitEndpoint(
              query.use_edge_identities,
              query.environmentId,
              query.identity,
            ),
          }
        },
      }),
      deleteIdentityTrait: builder.mutation<
        Res['identityTrait'],
        Req['deleteIdentityTrait']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'IdentityTrait' }],
        query: (query: Req['deleteIdentityTrait']) => {
          if (query.use_edge_identities) {
            return {
              body: getTraitBody(
                query.use_edge_identities,
                query.identity,
                query.data,
              ),
              method: 'PUT',
              url: getUpdateTraitEndpoint(
                query.use_edge_identities,
                query.environmentId,
                query.identity,
              ),
            }
          }
          return {
            body: {},
            method: 'DELETE',
            url: getUpdateTraitEndpoint(
              query.use_edge_identities,
              query.environmentId,
              query.identity,
            ),
          }
        },
      }),
      getIdentityTraits: builder.query<
        Res['identityTraits'],
        Req['getIdentityTraits']
      >({
        providesTags: [{ id: 'LIST', type: 'IdentityTrait' }],
        query: (query) => ({
          url: getTraitEndpoint(
            query.use_edge_identities,
            query.environmentId,
            query.identity,
          ),
        }),
      }),
      updateIdentityTrait: builder.mutation<
        Res['identityTrait'],
        Req['updateIdentityTrait']
      >({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'IdentityTrait' },
          { id: res?.id, type: 'IdentityTrait' },
        ],
        query: (query: Req['createIdentityTrait']) => {
          return {
            body: getTraitBody(
              query.use_edge_identities,
              query.identity,
              query.data,
            ),
            method: query.use_edge_identities ? 'PUT' : 'POST',
            url: getUpdateTraitEndpoint(
              query.use_edge_identities,
              query.environmentId,
              query.identity,
              query.data.id,
            ),
          }
        },
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createIdentityTrait(
  store: any,
  data: Req['createIdentityTrait'],
  options?: Parameters<
    typeof identityTraitService.endpoints.createIdentityTrait.initiate
  >[1],
) {
  return store.dispatch(
    identityTraitService.endpoints.createIdentityTrait.initiate(data, options),
  )
}
export async function getIdentityTraits(
  store: any,
  data: Req['getIdentityTraits'],
  options?: Parameters<
    typeof identityTraitService.endpoints.getIdentityTraits.initiate
  >[1],
) {
  return store.dispatch(
    identityTraitService.endpoints.getIdentityTraits.initiate(data, options),
  )
}
export async function updateIdentityTrait(
  store: any,
  data: Req['updateIdentityTrait'],
  options?: Parameters<
    typeof identityTraitService.endpoints.updateIdentityTrait.initiate
  >[1],
) {
  return store.dispatch(
    identityTraitService.endpoints.updateIdentityTrait.initiate(data, options),
  )
}
export async function deleteIdentityTrait(
  store: any,
  data: Req['deleteIdentityTrait'],
  options?: Parameters<
    typeof identityTraitService.endpoints.deleteIdentityTrait.initiate
  >[1],
) {
  return store.dispatch(
    identityTraitService.endpoints.deleteIdentityTrait.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateIdentityTraitMutation,
  useDeleteIdentityTraitMutation,
  useGetIdentityTraitsQuery,
  useUpdateIdentityTraitMutation,
  // END OF EXPORTS
} = identityTraitService

/* Usage examples:
const { data, isLoading } = useGetIdentityTraitQuery({ id: 2 }, {}) //get hook
const [createIdentityTrait, { isLoading, data, isSuccess }] = useCreateIdentityTraitMutation() //create hook
identityTraitService.endpoints.getIdentityTrait.select({id: 2})(store.getState()) //access data from any function
*/
