import React, { FC, FormEvent, useState } from 'react'
import ModalHR from './ModalHR'
import { ProjectFlag } from 'common/types/responses'
import ProjectProvider from 'common/providers/ProjectProvider'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils' // we need this to make JSX compile
import Button from 'components/base/forms/Button'

type ConfirmRemoveFeatureType = {
  cb: () => void
  projectFlag: ProjectFlag
  identity?: string
}

const ConfirmRemoveFeature: FC<ConfirmRemoveFeatureType> = ({
  cb,
  identity,
  projectFlag,
}) => {
  const [challenge, setChallenge] = useState()
  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (challenge == projectFlag.name) {
      closeModal()
      cb()
    }
  }

  return (
    <ProjectProvider>
      {() => (
        <form id='confirm-remove-feature-modal' onSubmit={submit}>
          <div className='modal-body'>
            <>
              {identity ? (
                <p>
                  This will reset <strong>{projectFlag.name}</strong> for to the
                  environment defaults for the user <strong>{identity}</strong>
                </p>
              ) : (
                <p>
                  This will remove <strong>{projectFlag.name}</strong> for{' '}
                  <strong>all environments</strong>. You should ensure that you
                  do not contain any references to this feature in your
                  applications before proceeding.
                </p>
              )}
              <InputGroup
                className='mb-0'
                inputProps={{
                  className: 'full-width',
                  name: 'confirm-feature-name',
                }}
                title='Please type the feature name to confirm'
                placeholder='feature_name'
                onChange={(e: InputEvent) =>
                  setChallenge(Utils.safeParseEventValue(e))
                }
              />
            </>
          </div>

          <ModalHR />
          <div className='modal-footer'>
            <Button className='mr-2' theme='secondary' onClick={closeModal}>
              Cancel
            </Button>
            <Button
              id='confirm-remove-feature-btn'
              type='submit'
              disabled={challenge != projectFlag.name}
              theme='primary'
            >
              Confirm changes
            </Button>
          </div>
        </form>
      )}
    </ProjectProvider>
  )
}

export default ConfirmRemoveFeature
