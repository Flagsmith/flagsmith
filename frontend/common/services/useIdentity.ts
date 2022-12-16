import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
const getIdentityEndpoint = (environmentId: string, isEdge:boolean)=> {
  const identityPart = isEdge? 'edge-identities' : 'identities';
  return `environments/${environmentId}/${identityPart}`
}



export const identityService = service
  .enhanceEndpoints({ addTagTypes: ['Identity'] })
    .injectEndpoints({
  endpoints: (builder) => ({

    createIdentities: builder.mutation<Res['identity'], Req['createIdentities']>({
      queryFn: async (query, _, _2, baseQuery) => {
        return Promise.all(
            query.identifiers.map((identifier)=>(
                baseQuery({
                  url: `${getIdentityEndpoint(query.environmentId, query.isEdge)}/`,
                  method: 'POST',
                  body: {
                    environment: query.environmentId,
                    identifier
                  }
                })
            ))
        ).then((res)=>{
          const erroredQuery = res.find((v)=>!!v?.error)
          return erroredQuery || res[res.length-1] // return any errored query or last query
        })
      },
      invalidatesTags: [{ type: 'Identity', id: 'LIST' }],
    }),
    deleteIdentity: builder.mutation<Res['identity'], Req['deleteIdentity']>({
      query: (query: Req['deleteIdentity']) => ({
        url: `${getIdentityEndpoint(query.environmentId, query.isEdge)}/${query.id}/`,
        method: 'DELETE',
        body: query,
      }),
      invalidatesTags: [{ type: 'Identity', id: 'LIST' },],
    }),
    getIdentities: builder.query<Res['identities'], Req['getIdentities']>({
      query: () => ({
        url: `identities`,
      }),
      providesTags:[{ type: 'Identity', id: 'LIST' },],
    }),
    // END OF ENDPOINTS
  }),
 })

export async function createIdentities(store: any, data: Req['createIdentities'], options?: Parameters<typeof identityService.endpoints.createIdentities.initiate>[1]) {
  store.dispatch(identityService.endpoints.createIdentities.initiate(data,options))
  return Promise.all(store.dispatch(identityService.util.getRunningQueriesThunk()))
}
  export async function deleteIdentity(store: any, data: Req['deleteIdentity'], options?: Parameters<typeof identityService.endpoints.deleteIdentity.initiate>[1]) {
  store.dispatch(identityService.endpoints.deleteIdentity.initiate(data,options))
  return Promise.all(store.dispatch(identityService.util.getRunningQueriesThunk()))
}
  export async function getIdentities(store: any, data: Req['getIdentities'], options?: Parameters<typeof identityService.endpoints.getIdentities.initiate>[1]) {
  store.dispatch(identityService.endpoints.getIdentities.initiate(data,options))
  return Promise.all(store.dispatch(identityService.util.getRunningQueriesThunk()))
}
  // END OF FUNCTION_EXPORTS

export const {
  useCreateIdentitiesMutation,
  useDeleteIdentityMutation,
  useGetIdentitiesQuery,
  // END OF EXPORTS
} = identityService

/* Usage examples:
const { data, isLoading } = useGetIdentityQuery({ id: 2 }, {}) //get hook
const [createIdentities, { isLoading, data, isSuccess }] = useCreateIdentitiesMutation() //create hook
identityService.endpoints.getIdentity.select({id: 2})(store.getState()) //access data from any function
*/
