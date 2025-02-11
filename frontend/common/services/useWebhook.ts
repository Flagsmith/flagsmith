import { service } from 'common/service'
import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'

export const webhookService = service
  .enhanceEndpoints({ addTagTypes: ['Webhooks'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createWebhook: builder.mutation<Res['webhook'], Req['createWebhook']>({
        invalidatesTags: [{ id: 'LIST', type: 'Webhooks' }],
        query: ({ environmentId, ...rest }) => ({
          body: {
            ...rest,
          },
          method: 'POST',
          url: `environments/${environmentId}/webhooks/`,
        }),
      }),

      deleteWebhook: builder.mutation<void, Req['deleteWebhook']>({
        invalidatesTags: [{ id: 'LIST', type: 'Webhooks' }],
        query: (query) => ({
          method: 'DELETE',
          url: `environments/${query.environmentId}/webhooks/${query.id}/`,
        }),
      }),

      getWebhooks: builder.query<Res['webhooks'], Req['getWebhooks']>({
        providesTags: [{ id: 'LIST', type: 'Webhooks' }],
        query: (query) => ({
          url: `environments/${query.environmentId}/webhooks/`,
        }),
      }),

      updateWebhook: builder.mutation<Res['webhook'], Req['updateWebhook']>({
        invalidatesTags: [{ id: 'LIST', type: 'Webhooks' }],
        query: ({ environmentId, ...rest }) => ({
          body: {
            ...rest,
          },
          method: 'PUT',
          url: `environments/${environmentId}/webhooks/${rest.id}/`,
        }),
      }),
    }),
  })

export const {
  useCreateWebhookMutation,
  useDeleteWebhookMutation,
  useGetWebhooksQuery,
  useUpdateWebhookMutation,
} = webhookService

/* Usage examples:
const { data, isLoading } = useGetWebhooksQuery({ environmentId: 1 }) //get hook
const [createWebhook, { isLoading, data, isSuccess }] = useCreateWebhookMutation() //create hook
webhookService.endpoints.getWebhooks.select({id: 2})(store.getState()) //access data from any function
*/
