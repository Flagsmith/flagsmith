import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import transformCorePaging from 'common/transformCorePaging'
import Utils from 'common/utils/utils'

const getIdentityEndpoint = (environmentId: string, isEdge: boolean) => {
  const identityPart = isEdge ? 'edge-identities' : 'identities'
  return `environments/${environmentId}/${identityPart}`
}

export const identityService = service
  .enhanceEndpoints({ addTagTypes: ['Identity'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createIdentities: builder.mutation<
        Res['identity'],
        Req['createIdentities']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'Identity' }],
        queryFn: async (query, _, _2, baseQuery) => {
          return Promise.all(
            query.identifiers.map((identifier) =>
              baseQuery({
                body: {
                  environment: query.environmentId,
                  identifier,
                },
                method: 'POST',
                url: `${getIdentityEndpoint(
                  query.environmentId,
                  query.isEdge,
                )}/`,
              }),
            ),
          ).then((res) => {
            const erroredQuery = res.find((v) => !!v?.error)
            return erroredQuery || res[res.length - 1] // return any errored query or last query
          })
        },
      }),
      deleteIdentity: builder.mutation<Res['identity'], Req['deleteIdentity']>({
        invalidatesTags: [{ id: 'LIST', type: 'Identity' }],
        query: (query: Req['deleteIdentity']) => ({
          body: query,
          method: 'DELETE',
          url: `${getIdentityEndpoint(query.environmentId, query.isEdge)}/${
            query.id
          }/`,
        }),
      }),
      getIdentities: builder.query<Res['identities'], Req['getIdentities']>({
        providesTags: [{ id: 'LIST', type: 'Identity' }],
        query: (baseQuery) => {
          const {
            dashboard_alias,
            environmentId,
            isEdge,
            page,
            page_size = 10,
            pageType,
            pages,
            q,
            search,
          } = baseQuery
          let url = `${getIdentityEndpoint(environmentId, isEdge)}/?q=${
            dashboard_alias ? 'dashboard_alias:' : ''
          }${encodeURIComponent(
            dashboard_alias || search || q || '',
          )}&page_size=${page_size}`
          let last_evaluated_key = null
          if (!isEdge) {
            url += `&page=${page}`
          }
          if (pageType === 'NEXT') {
            last_evaluated_key = pages?.[pages.length - 1]
          } else if (pageType === 'PREVIOUS') {
            last_evaluated_key = pages?.length ? pages[pages.length - 1] : null
          }
          if (last_evaluated_key) {
            url += `&last_evaluated_key=${encodeURIComponent(
              last_evaluated_key,
            )}`
          }

          return {
            url,
          }
        },
        transformResponse(baseQueryReturnValue: Res['identities'], meta, req) {
          const {
            isEdge,
            page = 1,
            page_size = 10,
            pageType,
            pages: _pages,
          } = req
          if (isEdge) {
            // For edge, we create our own paging
            let pages = _pages ? _pages.concat([]) : []
            const next_evaluated_key = baseQueryReturnValue.last_evaluated_key
            if (pageType === 'NEXT') {
              pages.push(next_evaluated_key)
            } else if (pageType === 'PREVIOUS') {
              pages.unshift()
            } else {
              pages = []
            }

            return {
              ...baseQueryReturnValue,
              next:
                baseQueryReturnValue.results.length < page_size
                  ? undefined
                  : '1',
              pages,
              //
              previous: pages.length ? '1' : undefined,
              results: baseQueryReturnValue.results?.map((v) => {
                if (v.id) {
                  return v
                }
                return {
                  ...v,
                  id: v.identity_uuid,
                }
              }), //
            }
          }
          return transformCorePaging(req, baseQueryReturnValue)
        },
      }),
      updateIdentity: builder.mutation<Res['identity'], Req['updateIdentity']>({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'Identity' },
          { id: res?.id, type: 'Identity' },
        ],
        query: (query: Req['updateIdentity']) => ({
          body: query.data,
          method: 'PUT',
          url: `environments/${
            query.environmentId
          }/${Utils.getIdentitiesEndpoint()}/${
            query.data.identity_uuid || query.data.id
          }`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createIdentities(
  store: any,
  data: Req['createIdentities'],
  options?: Parameters<
    typeof identityService.endpoints.createIdentities.initiate
  >[1],
) {
  store.dispatch(
    identityService.endpoints.createIdentities.initiate(data, options),
  )
  return Promise.all(
    store.dispatch(identityService.util.getRunningQueriesThunk()),
  )
}
export async function deleteIdentity(
  store: any,
  data: Req['deleteIdentity'],
  options?: Parameters<
    typeof identityService.endpoints.deleteIdentity.initiate
  >[1],
) {
  store.dispatch(
    identityService.endpoints.deleteIdentity.initiate(data, options),
  )
  return Promise.all(
    store.dispatch(identityService.util.getRunningQueriesThunk()),
  )
}
export async function getIdentities(
  store: any,
  data: Req['getIdentities'],
  options?: Parameters<
    typeof identityService.endpoints.getIdentities.initiate
  >[1],
) {
  store.dispatch(
    identityService.endpoints.getIdentities.initiate(data, options),
  )
  return Promise.all(
    store.dispatch(identityService.util.getRunningQueriesThunk()),
  )
}
export async function updateIdentity(
  store: any,
  data: Req['updateIdentity'],
  options?: Parameters<
    typeof identityService.endpoints.updateIdentity.initiate
  >[1],
) {
  return store.dispatch(
    identityService.endpoints.updateIdentity.initiate(data, options),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateIdentitiesMutation,
  useDeleteIdentityMutation,
  useGetIdentitiesQuery,
  useUpdateIdentityMutation,
  // END OF EXPORTS
} = identityService

/* Usage examples:
const { data, isLoading } = useGetIdentityQuery({ id: 2 }, {}) //get hook
const [createIdentities, { isLoading, data, isSuccess }] = useCreateIdentitiesMutation() //create hook
identityService.endpoints.getIdentity.select({id: 2})(store.getState()) //access data from any function
*/
