// import propTypes from 'prop-types';
import React, { FC, useState } from 'react' // we need this to make JSX compile
import ErrorMessage from './ErrorMessage'
import SuccessMessage from './SuccessMessage'
import data from 'common/data/base/_data'
import Button from './base/forms/Button'
import { useTestWebhookMutation } from 'common/services/useWebhooks'

type TestWebhookType = {
  webhookUrl: string | undefined
  json: string
  secret: string | undefined
  environmentId: string
}

// from https://stackoverflow.com/questions/24834812/space-in-between-json-stringify-output
const stringifyWithSpaces = (str: string) => {
  const obj = JSON.parse(str)
  let result = JSON.stringify(obj, null, 1) // stringify, with line-breaks and indents
  result = result.replace(/^ +/gm, ' ') // remove all but the first space for each line
  result = result.replace(/\n/g, '') // remove line-breaks
  result = result.replace(/{ /g, '{').replace(/ }/g, '}') // remove spaces between object-braces and first/last props
  result = result.replace(/\[ /g, '[').replace(/ \]/g, ']') // remove spaces between array-brackets and first/last items
  return result
}

const signPayload = async (body: string, secret: string): Promise<string> => {
  if (!secret) {
    return ''
  }
  const enc = new TextEncoder()

  const key = await window.crypto.subtle.importKey(
    'raw',
    enc.encode(secret),
    {
      hash: { name: 'SHA-256' },
      name: 'HMAC',
    },
    false,
    ['sign'],
  )

  const signature = await window.crypto.subtle.sign(
    'HMAC',
    key,
    enc.encode(stringifyWithSpaces(body)), // We do this bc the python output is single line with one space before each value
  )
  const signatureUnsignedIntArray = new Uint8Array(signature)
  return Array.prototype.map
    .call(signatureUnsignedIntArray, (element) =>
      element.toString(16).padStart(2, '0'),
    )
    .join('')
}

const TestWebhook: FC<TestWebhookType> = ({
  json,
  secret,
  webhookUrl: webhook,
  environmentId,
}) => {
  const [testWebhook, { isLoading, isError }] = useTestWebhookMutation()
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const submit = () => {
    setError(null)
    setLoading(true)
    setSuccess(false)
    signPayload(json, secret || '').then((sign) => {
      const headers = {
        'X-Flagsmith-Signature': sign,
      }
      data
        .post(webhook, JSON.parse(json), headers)
        .then(() => {
          setLoading(false)
          setSuccess(true)
        })
        .catch((e: any) => {
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
        // onClick={submit}
        onClick={() =>
          testWebhook({
            environmentId: environmentId,
            url: webhook,
            body: JSON.parse(json),
          })
        }
        theme='secondary'
      >
        Test your webhook
      </Button>
    </div>
  )
}

export default TestWebhook
