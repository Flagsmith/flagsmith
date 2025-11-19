import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import { sortBy } from 'lodash'

export const projectService = service
  .enhanceEndpoints({ addTagTypes: ['Project'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      deleteProject: builder.mutation<void, Req['deleteProject']>({
        invalidatesTags: [{ id: 'LIST', type: 'Project' }],
        query: ({ id }: Req['deleteProject']) => ({
          method: 'DELETE',
          url: `projects/${id}/`,
        }),
      }),
      getProject: builder.query<Res['project'], Req['getProject']>({
        providesTags: (res) => [{ id: res?.id, type: 'Project' }],
        query: (query: Req['getProject']) => ({
          url: `projects/${query.id}/`,
        }),
      }),
      getProjectPermissions: builder.query<
        Res['userPermissions'],
        Req['getProjectPermissions']
      >({
        query: ({ projectId }: Req['getProjectPermissions']) => ({
          url: `projects/${projectId}/user-permissions/`,
        }),
      }),
      getProjects: builder.query<Res['projects'], Req['getProjects']>({
        providesTags: [{ id: 'LIST', type: 'Project' }],
        query: (data) => ({
          url: `projects/?organisation=${data.organisationId}`,
        }),
        transformResponse: (res) => sortBy(res, (v) => v.name.toLowerCase()),
      }),
      migrateProject: builder.mutation<void, Req['migrateProject']>({
        invalidatesTags: (res, error, { id }) => [{ id, type: 'Project' }],
        query: ({ id }: Req['migrateProject']) => ({
          method: 'POST',
          url: `projects/${id}/migrate-to-edge/`,
        }),
      }),
      updateProject: builder.mutation<Res['project'], Req['updateProject']>({
        invalidatesTags: (res) => [
          { id: res?.id, type: 'Project' },
          { id: 'LIST', type: 'Project' },
        ],
        query: ({ body, id }: Req['updateProject']) => ({
          body,
          method: 'PUT',
          url: `projects/${id}/`,
        }),
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
export async function getProject(
  store: any,
  data: Req['getProject'],
  options?: Parameters<typeof projectService.endpoints.getProject.initiate>[1],
) {
  store.dispatch(projectService.endpoints.getProject.initiate(data, options))
  return Promise.all(
    store.dispatch(projectService.util.getRunningQueriesThunk()),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useDeleteProjectMutation,
  useGetProjectPermissionsQuery,
  useGetProjectQuery,
  useGetProjectsQuery,
  useMigrateProjectMutation,
  useUpdateProjectMutation,
  // END OF EXPORTS
} = projectService

/* Usage examples:
const { data, isLoading } = useGetProjectsQuery({ id: 2 }, {}) //get hook
const [createProjects, { isLoading, data, isSuccess }] = useCreateProjectsMutation() //create hook
projectService.endpoints.getProjects.select({id: 2})(store.getState()) //access data from any function
*/
