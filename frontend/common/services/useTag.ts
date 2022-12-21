import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const tagService = service
  .enhanceEndpoints({ addTagTypes: ['Tag'] })
    .injectEndpoints({
  endpoints: (builder) => ({
    updateTag: builder.mutation<Res['tag'], Req['updateTag']>({
      query: (query: Req['updateTag']) => ({
        url: `projects/${query.projectId}/tags/${query.tag.id}`,
        method: 'PUT',
        body: query.tag,
      }),
      invalidatesTags:(res)=>[{ type: 'Tag', id: 'LIST' },{ type: 'Tag', id: res?.id },],
    }),
    deleteTag: builder.mutation<Res['tag'], Req['deleteTag']>({
      query: (query: Req['deleteTag']) => ({
        url: `projects/${query.projectId}/${query.id}/`,
        method: 'DELETE',
        body: {},
      }),
      invalidatesTags: [{ type: 'Tag', id: 'LIST' },],
    }),
    getTags: builder.query<Res['tags'], Req['getTags']>({
      query: (query: Req['getTags']) => ({
        url: `projects/${query.projectId}/tags/`,
      }),
      providesTags:[{ type: 'Tag', id: 'LIST' },],
    }),
    createTag: builder.mutation<Res['tag'], Req['createTag']>({
      query: (query: Req['createTag']) => ({
        url: `tag`,
        method: 'POST',
        body: query,
      }),
      invalidatesTags: [{ type: 'Tag', id: 'LIST' }],
    }),
    // END OF ENDPOINTS
  }),
 })

export async function updateTag(store: any, data: Req['updateTag'], options?: Parameters<typeof tagService.endpoints.updateTag.initiate>[1]) {
  store.dispatch(tagService.endpoints.updateTag.initiate(data,options))
  return Promise.all(store.dispatch(tagService.util.getRunningQueriesThunk()))
}
  export async function deleteTag(store: any, data: Req['deleteTag'], options?: Parameters<typeof tagService.endpoints.deleteTag.initiate>[1]) {
  store.dispatch(tagService.endpoints.deleteTag.initiate(data,options))
  return Promise.all(store.dispatch(tagService.util.getRunningQueriesThunk()))
}
  export async function getTags(store: any, data: Req['getTags'], options?: Parameters<typeof tagService.endpoints.getTags.initiate>[1]) {
  store.dispatch(tagService.endpoints.getTags.initiate(data,options))
  return Promise.all(store.dispatch(tagService.util.getRunningQueriesThunk()))
}
  export async function createTag(store: any, data: Req['createTag'], options?: Parameters<typeof tagService.endpoints.createTag.initiate>[1]) {
  store.dispatch(tagService.endpoints.createTag.initiate(data,options))
  return Promise.all(store.dispatch(tagService.util.getRunningQueriesThunk()))
}
  // END OF FUNCTION_EXPORTS

export const {
  useUpdateTagMutation,
  useDeleteTagMutation,
  useGetTagsQuery,
  useCreateTagMutation,
  // END OF EXPORTS
} = tagService

/* Usage examples:
const { data, isLoading } = useGetTagQuery({ id: 2 }, {}) //get hook
const [createTag, { isLoading, data, isSuccess }] = useCreateTagMutation() //create hook
tagService.endpoints.getTag.select({id: 2})(store.getState()) //access data from any function
*/
