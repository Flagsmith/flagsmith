import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const launchDarklyService = service
  .enhanceEndpoints({ addTagTypes: ['launchDarklyProjectImport'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createLaunchDarklyProjectImport: builder.mutation<
        Res['launchDarklyProjectImport'],
        Req['createLaunchDarklyProjectImport']
      >({
        invalidatesTags: [{ id: 'LIST', type: 'launchDarklyProjectImport' }],
        query: (query: Req['createLaunchDarklyProjectImport']) => ({
          body: query.body,
          method: 'POST',
          url: `projects/${query.project_id}/imports/launch-darkly/`,
        }),
      }),
      getLaunchDarklyProjectImport: builder.query<
        Res['launchDarklyProjectImport'],
        Req['getLaunchDarklyProjectImport']
      >({
        providesTags: [{ id: 'LIST', type: 'launchDarklyProjectImport' }],
        query: (query) => ({
          url: `projects/${query.project_id}/imports/launch-darkly/${query.import_id}/`,
        }),
      }),
      getLaunchDarklyProjectsImport: builder.query<
        Res['launchDarklyProjectsImport'],
        Req['getLaunchDarklyProjectsImport']
      >({
        providesTags: [{ id: 'LIST', type: 'launchDarklyProjectImport' }],
        query: (query) => ({
          url: `projects/${query.project_id}/imports/launch-darkly/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createLaunchDarklyProjectImport(
  store: any,
  data: Req['createLaunchDarklyProjectImport'],
  options?: Parameters<
    typeof launchDarklyService.endpoints.createLaunchDarklyProjectImport.initiate
  >[1],
) {
  return store.dispatch(
    launchDarklyService.endpoints.createLaunchDarklyProjectImport.initiate(
      data,
      options,
    ),
  )
}
export async function getLaunchDarklyProjectImport(
  store: any,
  data: Req['getLaunchDarklyProjectImport'],
  options?: Parameters<
    typeof launchDarklyService.endpoints.getLaunchDarklyProjectImport.initiate
  >[1],
) {
  return store.dispatch(
    launchDarklyService.endpoints.getLaunchDarklyProjectImport.initiate(
      data,
      options,
    ),
  )
}
export async function getLaunchDarklyProjectsImport(
  store: any,
  data: Req['getLaunchDarklyProjectsImport'],
  options?: Parameters<
    typeof launchDarklyService.endpoints.getLaunchDarklyProjectsImport.initiate
  >[1],
) {
  return store.dispatch(
    launchDarklyService.endpoints.getLaunchDarklyProjectsImport.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateLaunchDarklyProjectImportMutation,
  useGetLaunchDarklyProjectImportQuery,
  useGetLaunchDarklyProjectsImportQuery,
  // END OF EXPORTS
} = launchDarklyService

/* Usage examples:
const { data, isLoading } = useGetLaunchDarklyProjectQuery({ id: 2 }, {}) //get hook
const [createLaunchDarklyProjectImport, { isLoading, data, isSuccess }] = useCreateLaunchDarklyProjectImportMutation() //create hook
launchDarklyService.endpoints.getLaunchDarklyProjectImport.select({id: 2})(store.getState()) //access data from any function
*/
