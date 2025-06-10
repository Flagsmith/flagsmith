import Constants from 'common/constants'
import { useGetEnvironmentQuery } from 'common/services/useEnvironment'
import { Webhook } from 'common/types/responses'
import Utils from 'common/utils/utils'
import ErrorMessage from 'components/ErrorMessage'
import Highlight from 'components/Highlight'
import TestWebhook from 'components/TestWebhook'
import ViewDocs from 'components/ViewDocs'
import { FC, useState, useRef, ChangeEvent } from 'react'

interface CreateWebhookProps {
  environmentId: string
  projectId: string
  webhook?: Webhook
  isEdit?: boolean
  save: (webhook: Partial<Webhook>) => Promise<any>
}

const exampleJSON = Constants.exampleWebhook

const CreateWebhook: FC<CreateWebhookProps> = ({
  environmentId,
  isEdit,
  save,
  webhook,
}) => {
  const [url, setUrl] = useState(isEdit ? webhook?.url : '')
  const [enabled, setEnabled] = useState(
    isEdit ? webhook?.enabled ?? true : true,
  )

  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState(false)
  const [secret, setSecret] = useState(isEdit ? webhook?.secret : '')
  const urlInputRef = useRef<HTMLInputElement>(null)
  const secretInputRef = useRef<HTMLInputElement>(null)
  const { data: environment } = useGetEnvironmentQuery({
    id: environmentId,
  })

  const handleSave = async () => {
    if (!url) return

    const webhookData: Partial<Webhook> = {
      enabled,
      secret,
      url,
    }

    if (isEdit && webhook) {
      webhookData.id = webhook.id
    }

    try {
      await save(webhookData)
      closeModal()
    } catch (error) {
      setError(true)
      setIsSaving(false)
    }
  }

  return (
    <div className='px-4'>
      <form
        className='mt-4'
        onSubmit={(e) => {
          e.preventDefault()
          handleSave()
        }}
      >
        <Row space>
          <Flex className='mb-4'>
            <div>
              <label>*URL (Expects a 200 response from POST)</label>
            </div>
            <Input
              ref={urlInputRef}
              value={url}
              onChange={(e: ChangeEvent<HTMLInputElement>) =>
                setUrl(Utils.safeParseEventValue(e))
              }
              isValid={!!url && url.length > 0}
              type='text'
              inputClassName='input--wide'
              placeholder='https://example.com/feature-changed/'
            />
          </Flex>
          <Row className='ms-4'>
            <Switch
              defaultChecked={enabled}
              checked={enabled}
              onChange={(value: boolean) => setEnabled(value)}
            />
            <span onClick={() => setEnabled(!enabled)} className='ms-2'>
              Enable
            </span>
          </Row>
        </Row>
        <Flex className='mb-4'>
          <div>
            <label>
              Secret (Optional) -{' '}
              <a
                className='text-info'
                target='_blank'
                href='https://docs.flagsmith.com/system-administration/webhooks#audit-log-web-hooks'
                rel='noreferrer'
              >
                More info
              </a>{' '}
            </label>
          </div>
          <Input
            ref={secretInputRef}
            value={secret}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setSecret(Utils.safeParseEventValue(e))
            }
            type='text'
            className='full-width'
            placeholder='Secret'
          />
        </Flex>
        <Flex className='mb-4'>
          {error && (
            <ErrorMessage error='Could not create a webhook for this url, please ensure you include http or https.' />
          )}
          <div className={isEdit ? 'footer' : ''}>
            <div className='mb-3'>
              <p className='text-dark fw-bold'>
                This will {isEdit ? 'update' : 'create'} a webhook for the
                environment <strong>{environment?.name}</strong>
              </p>
            </div>
            <div className='justify-content-end flex-row gap-3'>
              <TestWebhook
                json={Constants.exampleWebhook}
                webhookUrl={url}
                secret={secret}
                scope={{
                  id: environmentId,
                  type: 'environment',
                }}
              />
              {isEdit ? (
                <Button
                  data-test='update-feature-btn'
                  id='update-feature-btn'
                  disabled={isSaving || !url}
                  type='submit'
                >
                  {isSaving ? 'Updating' : 'Update Webhook'}
                </Button>
              ) : (
                <Button type='submit' disabled={isSaving || !url}>
                  {isSaving ? 'Creating' : 'Create Webhook'}
                </Button>
              )}
            </div>
          </div>
        </Flex>
        <FormGroup className='ml-1'>
          <div>
            <Row className='mb-3' space>
              <div className='font-weight-medium text-dark'>
                Example Payload
              </div>
              <ViewDocs href='https://docs.flagsmith.com/system-administration/webhooks#environment-web-hooks' />
            </Row>
            <Highlight
              forceExpanded
              style={{ marginBottom: 10 }}
              className='json'
            >
              {exampleJSON}
            </Highlight>
          </div>
        </FormGroup>
      </form>
    </div>
  )
}

export default CreateWebhook
