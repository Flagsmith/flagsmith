import React, { useState, useRef, FormEvent, ChangeEvent } from 'react'
import Constants from 'common/constants'
import ConfigProvider from 'common/providers/ConfigProvider'
import Highlight from 'components/Highlight'
import ErrorMessage from 'components/ErrorMessage'
import TestWebhook from 'components/TestWebhook'
import ViewDocs from 'components/ViewDocs'
import Button from 'components/base/forms/Button'
import AccountStore from 'common/stores/account-store'
import Utils from 'common/utils/utils'
import Input from 'components/base/forms/Input'
import Switch from 'components/Switch'
import { Webhook } from 'common/types/responses'
import {
  useCreateAuditLogWebhooksMutation,
  useUpdateAuditLogWebhooksMutation,
} from 'common/services/useAuditLogWebhook'

type Props = {
  webhook?: Webhook
  organisationId: string
}

const CreateAuditLogWebhook: React.FC<Props> = ({
  organisationId,
  webhook,
}) => {
  const [create, { error: createError, isLoading: isCreating }] =
    useCreateAuditLogWebhooksMutation({})
  const [update, { error: updateError, isLoading: isUpdating }] =
    useUpdateAuditLogWebhooksMutation({})
  const isSaving = isUpdating || isCreating
  const error = updateError || createError
  const isEdit = !!webhook
  const [enabled, setEnabled] = useState(
    isEdit ? webhook?.enabled ?? true : true,
  )
  const [secret, setSecret] = useState(isEdit ? webhook?.secret : '')
  const [url, setUrl] = useState(isEdit ? webhook?.url : '')
  const inputRef = useRef<any>(null)

  const handleSave = () => {
    if (!url) return
    const auditWebhook: Omit<Webhook, 'id' | 'created_at' | 'updated_at'> & {
      id?: number
    } = {
      enabled,
      secret: secret || '',
      url,
    }
    if (isEdit && webhook) {
      auditWebhook.id = webhook.id
    }

    const func = isEdit ? update : create

    func({ data: auditWebhook as any, organisationId }).then((res: any) => {
      if (!res?.error) {
        closeModal()
        toast(`${isEdit ? 'Updated' : 'Created'} webhook`)
      }
    })
  }

  return (
    <div className='px-4'>
      <form
        className='mt-4'
        onSubmit={(e: FormEvent<HTMLFormElement>) => {
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
              ref={inputRef}
              value={url}
              onChange={(e: ChangeEvent<HTMLInputElement>) =>
                setUrl(Utils.safeParseEventValue(e))
              }
              isValid={!!url && url.length > 0}
              type='text'
              inputClassName='input--wide'
              placeholder='https://example.com/audit/'
            />
          </Flex>
          <Row className='ms-4'>
            <Switch
              defaultChecked={enabled}
              checked={enabled}
              onChange={(val: boolean) => setEnabled(val)}
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
                href='https://docs.flagsmith.com/system-administration/webhooks#web-hook-signature'
                rel='noreferrer'
              >
                More info
              </a>{' '}
            </label>
          </div>
          <Input
            ref={inputRef}
            value={secret}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setSecret(Utils.safeParseEventValue(e))
            }
            isValid={!!url && url.length > 0}
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
                Organization{' '}
                <strong>{AccountStore.getOrganisation().name}</strong>
              </p>
            </div>
            <div className='justify-content-end flex-row'>
              <TestWebhook
                json={Constants.exampleAuditWebhook}
                webhook={url}
                secret={secret}
              />
              {isEdit ? (
                <Button
                  className='ml-3'
                  type='submit'
                  data-test='update-feature-btn'
                  id='update-feature-btn'
                  disabled={isSaving || !url}
                  size='small'
                >
                  {isSaving ? 'Updating' : 'Update Webhook'}
                </Button>
              ) : (
                <Button
                  className='ml-3'
                  type='submit'
                  disabled={isSaving || !url}
                  size='small'
                >
                  {isSaving ? 'Creating' : 'Create Webhook'}
                </Button>
              )}
            </div>
          </div>
        </Flex>
        <FormGroup className='ml-1'>
          <div>
            <Row className='mb-3' space>
              <div className='font-weight-medium'>Example Payload </div>
              <ViewDocs href='https://docs.flagsmith.com/system-administration/webhooks#audit-log-web-hooks' />
            </Row>
            <Highlight forceExpanded className='json mb-2'>
              {Constants.exampleAuditWebhook}
            </Highlight>
          </div>
        </FormGroup>
      </form>
    </div>
  )
}

export default ConfigProvider(CreateAuditLogWebhook)
