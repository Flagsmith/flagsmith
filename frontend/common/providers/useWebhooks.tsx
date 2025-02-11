import {
  useCreateWebhookMutation,
  useDeleteWebhookMutation,
  useGetWebhooksQuery,
  useUpdateWebhookMutation,
} from 'common/services/useWebhook'

export const useWebhooks = (environmentId: string) => {
  const { data: webhooks, isLoading } = useGetWebhooksQuery(
    { environmentId },
    { refetchOnFocus: false, skip: !environmentId },
  )
  const [createWebhook] = useCreateWebhookMutation()
  const [updateWebhook] = useUpdateWebhookMutation()
  const [deleteWebhook] = useDeleteWebhookMutation()

  return {
    createWebhook,
    deleteWebhook,
    isLoading,
    updateWebhook,
    webhooks,
  }
}
