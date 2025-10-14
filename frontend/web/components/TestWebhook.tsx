import React, { FC } from 'react'
import ErrorMessage from './messages/ErrorMessage'
import SuccessMessage from './messages/SuccessMessage'
import Button from './base/forms/Button'
import { useTestWebhookMutation } from 'common/services/useWebhooks'

type TestWebhookType = {
  webhookUrl: string | undefined
  json: string
  secret: string | undefined
  scope: {
    type: 'environment' | 'organisation'
    id: string
  }
}

const TestWebhook: FC<TestWebhookType> = ({ scope, secret, webhookUrl }) => {
  const [
    testWebhook,
    { error: backendError, isLoading, isSuccess: isBackendSuccess },
  ] = useTestWebhookMutation()
  return (
    <>
      {backendError && (
        <ErrorMessage
          error={backendError}
          errorStyles={{ marginBottom: '0' }}
        />
      )}
      {isBackendSuccess && (
        <div style={{ maxWidth: 'fit-content' }}>
          <SuccessMessage
            successStyles={{
              marginBottom: '0',
              width: 'fit-content !important',
            }}
          >
            {'Your API returned with a successful 200 response.'}
          </SuccessMessage>
        </div>
      )}
      <div>
        <Button
          type='button'
          id='try-it-btn'
          disabled={isLoading || !webhookUrl}
          onClick={() => {
            if (!webhookUrl) {
              return
            }
            testWebhook({
              scope,
              secret: secret ?? undefined,
              webhookUrl,
            })
          }}
          theme='secondary'
        >
          Test your webhook
        </Button>
      </div>
    </>
  )
}

export default TestWebhook
