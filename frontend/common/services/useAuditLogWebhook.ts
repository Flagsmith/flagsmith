import { Res } from 'common/types/responses'
import { Req } from 'common/types/requests'
import { service } from 'common/service'

export const organisationWebhookService = service
  .enhanceEndpoints({ addTagTypes: ['AuditLogWebhook'] })
  .injectEndpoints({
    endpoints: (builder) => ({
      createAuditLogWebhooks: builder.mutation<
        Res['organisationWebhooks'],
        Req['createAuditLogWebhooks']
      >({
        invalidatesTags: (res, _, req) => [
          { id: req?.organisationId, type: 'AuditLogWebhook' },
        ],
        query: (query: Req['createAuditLogWebhooks']) => ({
          body: query.data,
          method: 'POST',
          url: `organisations/${query.organisationId}/webhooks/`,
        }),
      }),
      deleteAuditLogWebhook: builder.mutation<
        Res['organisationWebhooks'],
        Req['deleteAuditLogWebhook']
      >({
        invalidatesTags: (res, _, req) => [
          { id: req?.organisationId, type: 'AuditLogWebhook' },
        ],
        query: (query: Req['deleteAuditLogWebhook']) => ({
          body: query,
          method: 'DELETE',
          url: `organisations/${query.organisationId}/webhooks/${query.id}/`,
        }),
      }),
      getAuditLogWebhooks: builder.query<
        Res['organisationWebhooks'],
        Req['getAuditLogWebhooks']
      >({
        providesTags: (res, _, req) => [
          { id: req?.organisationId, type: 'AuditLogWebhook' },
        ],
        query: (query: Req['getAuditLogWebhooks']) => ({
          url: `organisations/${query.organisationId}/webhooks/`,
        }),
      }),
      updateAuditLogWebhooks: builder.mutation<
        Res['organisationWebhooks'],
        Req['updateAuditLogWebhooks']
      >({
        invalidatesTags: (res, _, req) => [
          { id: req?.organisationId, type: 'AuditLogWebhook' },
        ],
        query: (query: Req['updateAuditLogWebhooks']) => ({
          body: query.data,
          method: 'PUT',
          url: `organisations/${query.organisationId}/webhooks/${query.data.id}/`,
        }),
      }),
      // END OF ENDPOINTS
    }),
  })

export async function createAuditLogWebhooks(
  store: any,
  data: Req['createAuditLogWebhooks'],
  options?: Parameters<
    typeof organisationWebhookService.endpoints.createAuditLogWebhooks.initiate
  >[1],
) {
  return store.dispatch(
    organisationWebhookService.endpoints.createAuditLogWebhooks.initiate(
      data,
      options,
    ),
  )
}
export async function deleteAuditLogWebhook(
  store: any,
  data: Req['deleteAuditLogWebhook'],
  options?: Parameters<
    typeof organisationWebhookService.endpoints.deleteAuditLogWebhook.initiate
  >[1],
) {
  return store.dispatch(
    organisationWebhookService.endpoints.deleteAuditLogWebhook.initiate(
      data,
      options,
    ),
  )
}
export async function getAuditLogWebhooks(
  store: any,
  data: Req['getAuditLogWebhooks'],
  options?: Parameters<
    typeof organisationWebhookService.endpoints.getAuditLogWebhooks.initiate
  >[1],
) {
  return store.dispatch(
    organisationWebhookService.endpoints.getAuditLogWebhooks.initiate(
      data,
      options,
    ),
  )
}
export async function updateAuditLogWebhooks(
  store: any,
  data: Req['updateAuditLogWebhooks'],
  options?: Parameters<
    typeof organisationWebhookService.endpoints.updateAuditLogWebhooks.initiate
  >[1],
) {
  return store.dispatch(
    organisationWebhookService.endpoints.updateAuditLogWebhooks.initiate(
      data,
      options,
    ),
  )
}
// END OF FUNCTION_EXPORTS

export const {
  useCreateAuditLogWebhooksMutation,
  useDeleteAuditLogWebhookMutation,
  useGetAuditLogWebhooksQuery,
  useUpdateAuditLogWebhooksMutation,
  // END OF EXPORTS
} = organisationWebhookService

/* Usage examples:
const { data, isLoading } = useGetAuditLogWebhooksQuery({ id: 2 }, {}) //get hook
const [createAuditLogWebhooks, { isLoading, data, isSuccess }] = useCreateAuditLogWebhooksMutation() //create hook
organisationWebhookService.endpoints.getAuditLogWebhooks.select({id: 2})(store.getState()) //access data from any function
*/
