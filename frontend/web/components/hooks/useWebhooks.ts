import { useEffect, useState } from 'react'
// @ts-ignore
import * as data from 'common/data/base/_data'
import Project from 'common/project'

interface WebhookType {
  id: string
  url: string
  enabled: boolean
  created_at: string
}

interface UseWebhooksParams {
  environmentId: string
}


export const useAPI = () => {
  useEffect(() => {
    // const token = AccountStore.getToken()
    data.setToken("3b6675da07587f2c582e2a99c13e25907d8f4856")
  }, [])

  return data
}

export const useWebhooks = ({ environmentId }: UseWebhooksParams) => {
  const [webhooks, setWebhooks] = useState<WebhookType[]>([])
  const [webhooksLoading, setWebhooksLoading] = useState(false)
  const api = useAPI()

  const getWebhooks = async () => {
    setWebhooksLoading(true)
    console.log("gettingWebhooks")
    try {
      const response = await api.get<WebhookType[]>(
        `${Project.api}environments/${environmentId}/webhooks/`
      )
      setWebhooks(response)
    } finally {
      setWebhooksLoading(false)
    }
  }

  const deleteWebhook = async (webhook: WebhookType) => {
    setWebhooksLoading(true)
    try {
      await data.delete(
        `${Project.api}environments/${environmentId}/webhooks/${webhook.id}/`
      )
      await getWebhooks()
    } finally {
      setWebhooksLoading(false)
    }
  }

  const saveWebhook = async (webhook: WebhookType) => {
    setWebhooksLoading(true)
    try {
      await data.put(
        `${Project.api}environments/${environmentId}/webhooks/${webhook.id}/`,
        webhook
      )
      await getWebhooks()
    } finally {
      setWebhooksLoading(false)
    }
  }

  const createWebhook = async (webhook: Partial<WebhookType>) => {
    setWebhooksLoading(true)
    try {
      await data.post(
        `${Project.api}environments/${environmentId}/webhooks/`,
        webhook
      )
      await getWebhooks()
    } finally {
      setWebhooksLoading(false)
    }
  }

  return {
    createWebhook,
    deleteWebhook,
    getWebhooks,
    saveWebhook,
    webhooks,
    webhooksLoading,
  }
}
