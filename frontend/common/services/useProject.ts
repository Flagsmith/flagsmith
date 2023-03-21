import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import { sortBy } from 'lodash'
export const projectService = service
  .enhanceEndpoints({ addTagTypes: ['Project'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      getProjects: builder.query<Res['projects'], Req['getProjects']>({
        providesTags: [{ id: 'LIST', type: 'Project' }],
        query: (data) => ({
          url: `projects/?organisation=${data.organisationId}`,
        }),
        transformResponse: (res) => sortBy(res, 'name'),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function getProjects(
  store: any,
  data: Req['getProjects'],
  options?: Parameters<typeof projectService.endpoints.getProjects.initiate>[1],
) {
  store.dispatch(projectService.endpoints.getProjects.initiate(data, options))
  return Promise.all(
    store.dispatch(projectService.util.getRunningQueriesThunk()),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useGetProjectsQuery,
  // END OF EXPORTS
} = projectService

/* Usage examples:
const { data, isLoading } = useGetProjectsQuery({ id: 2 }, {}) //get hook
const [createProjects, { isLoading, data, isSuccess }] = useCreateProjectsMutation() //create hook
projectService.endpoints.getProjects.select({id: 2})(store.getState()) //access data from any function
*/
