import React, { FC, FormEvent, useState } from 'react'
import Button from 'components/base/forms/Button'
import Utils from 'common/utils/utils'
import InputGroup from 'components/base/forms/InputGroup' // we need this to make JSX compile
import ProjectProvider from 'common/providers/ProjectProvider'
import { Organisation } from 'common/types/responses'
import ModalHR from './ModalHR'

type ConfirmRemoveOrganisationType = {
  organisation: Organisation
  cb: () => void
}

const ConfirmRemoveOrganisation: FC<ConfirmRemoveOrganisationType> = ({
  cb,
  organisation,
}) => {
  const [challenge, setChallenge] = useState()

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (challenge == organisation.name) {
      closeModal()
      cb()
    }
  }
  return (
    <ProjectProvider>
      {() => (
        <form onSubmit={submit}>
          <div className='modal-body'>
            <>
              This will remove <strong>{organisation.name}</strong> and{' '}
              <strong>all of it's projects</strong>. You should ensure that you
              do not contain any references to this organisation in your
              applications before proceeding. This action cannot be undone.
            </>
            <InputGroup
              className='mb-0'
              inputProps={{ className: 'full-width', name: 'confirm-org-name' }}
              title='Please type the organisation name to confirm'
              placeholder='Organisation name'
              onChange={(e: InputEvent) =>
                setChallenge(Utils.safeParseEventValue(e))
              }
            />
          </div>
          <ModalHR />
          <div className='modal-footer'>
            <Button onClick={closeModal} theme='secondary' className='mr-2'>
              Cancel
            </Button>
            <Button
              id='confirm-del-org-btn'
              type='submit'
              theme='danger'
              disabled={challenge != organisation.name}
            >
              Confirm
            </Button>
          </div>
        </form>
      )}
    </ProjectProvider>
  )
}

export default ConfirmRemoveOrganisation
