import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const permissionService = service
  .enhanceEndpoints({ addTagTypes: ['Permission'] })
    .injectEndpoints({
  endpoints: (builder) => ({
    getPermission: builder.query<Res['permission'], Req['getPermission']>({
      query: ({level,id}: Req['getPermission']) => ({
        url: `${level}s/${id}/my-permissions/`,
      }),
      transformResponse(baseQueryReturnValue: {admin:boolean, permissions:string[]}) {
        let res:Res['permission'] = {
          ADMIN: baseQueryReturnValue.admin
        }
        baseQueryReturnValue.permissions.forEach((v)=>{
          res[v] = true
        })
        return res
      },
      providesTags:(res,err,req)=>{
        return [{ type: 'Permission', id: `${req.level}${req.id}` },]
      },
    }),
    // END OF ENDPOINTS
  }),
 })

export async function getPermission(store: any, data: Req['getPermission'], options?: Parameters<typeof permissionService.endpoints.getPermission.initiate>[1]) {
  store.dispatch(permissionService.endpoints.getPermission.initiate(data,options))
  return Promise.all(store.dispatch(permissionService.util.getRunningQueriesThunk()))
}
  // END OF FUNCTION_EXPORTS

export const {
  useGetPermissionQuery,
  // END OF EXPORTS
} = permissionService

/* Usage examples:
const { data, isLoading } = useGetPermissionQuery({ id: 2 }, {}) //get hook
const [createPermission, { isLoading, data, isSuccess }] = useCreatePermissionMutation() //create hook
permissionService.endpoints.getPermission.select({id: 2})(store.getState()) //access data from any function
*/
