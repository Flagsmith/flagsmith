import React, { FC, FormEvent, useState } from 'react'
import { useGetEnvironmentQuery } from 'common/services/useEnvironment'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import Button from 'components/base/forms/Button'
import ModalHR from './ModalHR'

type ConfirmRemoveWebhookType = {
  url: string
  cb: () => void
  environmentId: string
}

const ConfirmRemoveWebhook: FC<ConfirmRemoveWebhookType> = ({
  cb,
  environmentId,
  url,
}) => {
  const [challenge, setChallenge] = useState()
  const { data: environment } = useGetEnvironmentQuery({ id: environmentId })

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (challenge == url) {
      closeModal()
      cb()
    }
  }

  return (
    <form id='confirm-remove-feature-modal' onSubmit={submit}>
      <div className='modal-body'>
        <p>
          This will remove webhooks to <strong>{url}</strong> for the
          environment <strong>{environment?.name}</strong>. This action cannot
          be undone.
        </p>
        <InputGroup
          className='mb-0'
          inputProps={{
            className: 'full-width',
            name: 'confirm-feature-name',
          }}
          title='Please type the webhook url to confirm'
          placeholder='webhook url'
          onChange={(e: InputEvent) => {
            setChallenge(Utils.safeParseEventValue(e))
          }}
        />
      </div>
      <ModalHR />
      <div className='modal-footer'>
        <Button onClick={closeModal} theme='secondary' className='mr-2'>
          Cancel
        </Button>
        <Button
          type='submit'
          theme='danger'
          id='confirm-remove-feature-btn'
          disabled={challenge != url}
        >
          Confirm
        </Button>
      </div>
    </form>
  )
}

export default ConfirmRemoveWebhook
