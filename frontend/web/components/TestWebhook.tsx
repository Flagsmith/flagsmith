// import propTypes from 'prop-types';
import React, { FC, useState } from 'react' // we need this to make JSX compile
import ErrorMessage from './ErrorMessage'
import SuccessMessage from './SuccessMessage'
import data from 'common/data/base/_data'
import Button from './base/forms/Button'

type TestWebhookType = {
  webhook: string
  json: string
}

const TestWebhook: FC<TestWebhookType> = ({ json, webhook }) => {
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const submit = () => {
    setError(null)
    setLoading(true)
    setSuccess(false)
    data
      .post(webhook, JSON.parse(json), null, true)
      .then(() => {
        setLoading(false)
        setSuccess(true)
      })
      .catch((e) => {
        if (e.text) {
          e.text().then((error: string) => {
            setError(`The server returned an error: ${error}`)
          })
        } else {
          setError('There was an error posting to your webhook.')
        }
      })
      .finally(() => {
        setLoading(false)
      })
  }
  return (
    <div>
      {error && <ErrorMessage error={error} />}
      {success && (
        <SuccessMessage message='Your API returned with a successful 200 response.' />
      )}
      <Button
        type='button'
        id='try-it-btn'
        disabled={loading || !webhook}
        onClick={submit}
        theme='secondary'
      >
        Test your webhook
      </Button>
    </div>
  )
}

export default TestWebhook
