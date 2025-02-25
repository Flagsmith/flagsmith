import React, { FC, FormEvent, useState } from 'react'
import AccountStore from 'common/stores/account-store'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import Button from 'components/base/forms/Button'
import ModalHR from './ModalHR' // we need this to make JSX compile

type ConfirmRemoveAuditWebhookType = {
  url: string
  cb: () => void
}

const ConfirmRemoveAuditWebhook: FC<ConfirmRemoveAuditWebhookType> = ({
  cb,
  url,
}) => {
  const [challenge, setChallenge] = useState()

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
          This will remove <strong>{url}</strong> for the organisation{' '}
          <strong>{AccountStore.getOrganisation().name}</strong>. You should
          ensure that you do not contain any references to this webhook in your
          applications before proceeding.
        </p>

        <InputGroup
          className='mb-0'
          inputProps={{ className: 'full-width', name: 'confirm-feature-name' }}
          title='Please type the webhook url to confirm'
          placeholder='webhook url'
          onChange={(e: InputEvent) =>
            setChallenge(Utils.safeParseEventValue(e))
          }
        />
      </div>
      <ModalHR />
      <div className='modal-footer'>
        <Button theme='secondary' className='mr-2' onClick={closeModal}>
          Cancel
        </Button>
        <Button
          id='confirm-remove-feature-btn'
          disabled={challenge != url}
          type='submit'
        >
          Confirm
        </Button>
      </div>
    </form>
  )
}

export default ConfirmRemoveAuditWebhook
