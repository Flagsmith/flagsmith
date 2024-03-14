import React, { FC, FormEvent, useState } from 'react'
import ModalHR from './ModalHR'
import Button from 'components/base/forms/Button'
import { Project } from 'common/types/responses'
import ProjectProvider from 'common/providers/ProjectProvider'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils' // we need this to make JSX compile

type ConfirmRemoveProjectType = {
  project: Project
  cb: () => void
}

const ConfirmRemoveProject: FC<ConfirmRemoveProjectType> = ({
  cb,
  project,
}) => {
  const [challenge, setChallenge] = useState()

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (challenge == project.name) {
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
              This will remove <strong>{project.name}</strong> and{' '}
              <strong>all environments</strong>. You should ensure that you do
              not contain any references to this project in your applications
              before proceeding. This action cannot be undone.
            </p>
            <InputGroup
              className='mb-0'
              inputProps={{ className: 'full-width' }}
              title='Please type the project name to confirm'
              placeholder='Project name'
              onChange={(e: InputEvent) =>
                setChallenge(Utils.safeParseEventValue(e))
              }
            />
          </div>

          <ModalHR />
          <div className='modal-footer'>
            <Button className='mr-2' onClick={closeModal} theme='secondary'>
              Cancel
            </Button>
            <Button
              theme='danger'
              disabled={challenge != project.name}
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

export default ConfirmRemoveProject
