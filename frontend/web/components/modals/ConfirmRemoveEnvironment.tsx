import React, { FC, FormEvent, useState } from 'react'
import ModalHR from './ModalHR'
import Button from 'components/base/forms/Button'
import { Environment } from 'common/types/responses'
import ProjectProvider from 'common/providers/ProjectProvider'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils' // we need this to make JSX compile

type ConfirmRemoveEnvironmentType = {
  environment: Environment
  cb: () => void
}

const ConfirmRemoveEnvironment: FC<ConfirmRemoveEnvironmentType> = ({
  cb,
  environment,
}) => {
  const [challenge, setChallenge] = useState()
  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (challenge == environment.name) {
      closeModal()
      cb()
    }
  }
  return (
    <ProjectProvider>
      {() => (
        <form onSubmit={submit}>
          <div className='modal-body'>
            <p>
              This will remove the environment{' '}
              <strong>{environment.name}</strong> from your project. You should
              ensure that you do not contain any references to this environment
              in your applications before proceeding.
            </p>
            <InputGroup
              className='mb-0'
              inputProps={{
                className: 'full-width',
                name: 'confirm-env-name',
              }}
              title='Please type the environment name to confirm'
              placeholder='Environment name'
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
              id='confirm-delete-env-btn'
              disabled={challenge != environment.name}
              type='submit'
            >
              Confirm
            </Button>
          </div>
        </form>
      )}
    </ProjectProvider>
  )
}
export default ConfirmRemoveEnvironment
