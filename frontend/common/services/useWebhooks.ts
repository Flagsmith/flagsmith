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

      testWebhook: builder.mutation<void, Req['testWebhook']>({
        query: (query) => {
          return {
            body: {
              scope: query.scope,
              secret: query.secret,
              webhook_url: query.webhookUrl,
            },
            method: 'POST',
            url: `webhooks/test/`,
          }
        },
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

export async function createWebhook(
  store: any,
  data: Req['createWebhook'],
  options?: Parameters<
    typeof webhookService.endpoints.createWebhook.initiate
  >[1],
) {
  return store.dispatch(
    webhookService.endpoints.createWebhook.initiate(data, options),
  )
}
export async function getWebhooks(
  store: any,
  data: Req['getWebhooks'],
  options?: Parameters<typeof webhookService.endpoints.getWebhooks.initiate>[1],
) {
  return store.dispatch(
    webhookService.endpoints.getWebhooks.initiate(data, options),
  )
}
export async function updateWebhook(
  store: any,
  data: Req['updateWebhook'],
  options?: Parameters<
    typeof webhookService.endpoints.updateWebhook.initiate
  >[1],
) {
  return store.dispatch(
    webhookService.endpoints.deleteWebhook.initiate(data, options),
  )
}
export async function deleteWebhook(
  store: any,
  data: Req['deleteWebhook'],
  options?: Parameters<
    typeof webhookService.endpoints.deleteWebhook.initiate
  >[1],
) {
  return store.dispatch(
    webhookService.endpoints.deleteWebhook.initiate(data, options),
  )
}

export const {
  useCreateWebhookMutation,
  useDeleteWebhookMutation,
  useGetWebhooksQuery,
  useTestWebhookMutation,
  useUpdateWebhookMutation,
} = webhookService

/* Usage examples:
const { data, isLoading } = useGetWebhooksQuery({ environmentId: 1 }) //get hook
const [createWebhook, { isLoading, data, isSuccess }] = useCreateWebhookMutation() //create hook
webhookService.endpoints.getWebhooks.select({id: 2})(store.getState()) //access data from any function
*/
