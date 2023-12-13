import { PagedResponse, Res, Tag } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'
import { sortBy } from 'lodash'

export const tagService = service
  .enhanceEndpoints({ addTagTypes: ['Tag'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createTag: builder.mutation<Res['tag'], Req['createTag']>({
        invalidatesTags: [{ id: 'LIST', type: 'Tag' }],
        query: (query: Req['createTag']) => ({
          body: query.tag,
          method: 'POST',
          url: `projects/${query.projectId}/tags/`,
        }),
      }),
      deleteTag: builder.mutation<Res['tag'], Req['deleteTag']>({
        invalidatesTags: [{ id: 'LIST', type: 'Tag' }],
        query: (query: Req['deleteTag']) => ({
          body: {},
          method: 'DELETE',
          url: `projects/${query.projectId}/tags/${query.id}/`,
        }),
      }),
      getTags: builder.query<Res['tags'], Req['getTags']>({
        providesTags: [{ id: 'LIST', type: 'Tag' }],
        query: (query: Req['getTags']) => ({
          url: `projects/${query.projectId}/tags/`,
        }),
        transformResponse(baseQueryReturnValue: PagedResponse<Tag>) {
          return sortBy(baseQueryReturnValue.results, 'label')
        },
      }),
      updateTag: builder.mutation<Res['tag'], Req['updateTag']>({
        invalidatesTags: (res) => [
          { id: 'LIST', type: 'Tag' },
          { id: res?.id, type: 'Tag' },
        ],
        query: (query: Req['updateTag']) => ({
          body: query.tag,
          method: 'PUT',
          url: `projects/${query.projectId}/tags/${query.tag.id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function updateTag(
  store: any,
  data: Req['updateTag'],
  options?: Parameters<typeof tagService.endpoints.updateTag.initiate>[1],
) {
  store.dispatch(tagService.endpoints.updateTag.initiate(data, options))
  return Promise.all(store.dispatch(tagService.util.getRunningQueriesThunk()))
}
export async function deleteTag(
  store: any,
  data: Req['deleteTag'],
  options?: Parameters<typeof tagService.endpoints.deleteTag.initiate>[1],
) {
  store.dispatch(tagService.endpoints.deleteTag.initiate(data, options))
  return Promise.all(store.dispatch(tagService.util.getRunningQueriesThunk()))
}
export async function getTags(
  store: any,
  data: Req['getTags'],
  options?: Parameters<typeof tagService.endpoints.getTags.initiate>[1],
) {
  store.dispatch(tagService.endpoints.getTags.initiate(data, options))
  return Promise.all(store.dispatch(tagService.util.getRunningQueriesThunk()))
}
export async function createTag(
  store: any,
  data: Req['createTag'],
  options?: Parameters<typeof tagService.endpoints.createTag.initiate>[1],
) {
  store.dispatch(tagService.endpoints.createTag.initiate(data, options))
  return Promise.all(store.dispatch(tagService.util.getRunningQueriesThunk()))
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateTagMutation,
  useDeleteTagMutation,
  useGetTagsQuery,
  useUpdateTagMutation,
  // END OF EXPORTS
} = tagService

/* Usage examples:
const { data, isLoading } = useGetTagQuery({ id: 2 }, {}) //get hook
const [createTag, { isLoading, data, isSuccess }] = useCreateTagMutation() //create hook
tagService.endpoints.getTag.select({id: 2})(store.getState()) //access data from any function
*/
