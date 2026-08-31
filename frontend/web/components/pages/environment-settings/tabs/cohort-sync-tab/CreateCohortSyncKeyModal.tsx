import React, { FC, useState } from 'react'
import { useCreateCohortSyncKeyMutation } from 'common/services/useCohort'
import Button from 'components/base/forms/Button'
import InputGroup from 'components/base/forms/InputGroup'
import CopyField from 'components/CopyField'
import ErrorMessage from 'components/ErrorMessage'
import ModalHR from 'components/modals/ModalHR'
import WarningMessage from 'components/WarningMessage'

const NAME_MAX_LENGTH = 50

type CreateCohortSyncKeyModalProps = {
  environmentApiKey: string
}

const CreateCohortSyncKeyModal: FC<CreateCohortSyncKeyModalProps> = ({
  environmentApiKey,
}) => {
  const [name, setName] = useState('')
  const [createdKey, setCreatedKey] = useState<string | null>(null)
  const [createCohortSyncKey, { error, isLoading }] =
    useCreateCohortSyncKeyMutation()

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    createCohortSyncKey({ environmentApiKey, name: name.trim() })
      .unwrap()
      .then((syncKey) => setCreatedKey(syncKey.key))
      .catch(() => {})
  }

  if (createdKey) {
    return (
      <div>
        <div className='modal-body'>
          <CopyField
            title='Cohort sync key'
            value={createdKey}
            className='font-monospace'
            data-test='cohort-sync-key-value'
          />
          <WarningMessage
            warningMessage='This key is shown only once. Store it securely — you will not be able to see it again.'
            warningMessageClass='mt-3'
          />
        </div>
        <ModalHR />
        <div className='modal-footer'>
          <Button onClick={() => closeModal()} data-test='cohort-sync-key-done'>
            Done
          </Button>
        </div>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit}>
      <div className='modal-body'>
        <InputGroup
          title='Name*'
          value={name}
          data-test='cohort-sync-key-name'
          inputProps={{
            className: 'full-width modal-input',
            maxLength: NAME_MAX_LENGTH,
            name: 'name',
          }}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
            setName(event.target.value)
          }
          isValid={!!name.trim().length}
          type='text'
          placeholder='e.g. Mixpanel production'
        />
        <ErrorMessage error={error} />
      </div>
      <ModalHR />
      <div className='modal-footer'>
        <Button onClick={() => closeModal()} theme='secondary' className='mr-2'>
          Cancel
        </Button>
        <Button
          type='submit'
          disabled={!name.trim() || isLoading}
          data-test='cohort-sync-key-create'
        >
          {isLoading ? 'Creating' : 'Create'}
        </Button>
      </div>
    </form>
  )
}

export default CreateCohortSyncKeyModal
