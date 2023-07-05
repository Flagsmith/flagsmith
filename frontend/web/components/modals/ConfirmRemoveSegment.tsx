import React, { FC, FormEvent, useState } from 'react'
import { Segment } from 'common/types/responses'
import ProjectProvider from 'common/providers/ProjectProvider'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils' // we need this to make JSX compile
import Button from 'components/base/forms/Button'
import ModalHR from './ModalHR'

type ConfirmRemoveSegmentType = {
  segment: Segment
  cb: () => void
}

const ConfirmRemoveSegment: FC<ConfirmRemoveSegmentType> = ({
  cb,
  segment,
}) => {
  const [challenge, setChallenge] = useState()

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (challenge == segment.name) {
      closeModal()
      cb()
    }
  }

  return (
    <ProjectProvider>
      {() => (
        <form id='confirm-remove-segment-modal' onSubmit={submit}>
          <div className='modal-body'>
            <p>
              This will remove <strong>{segment.name}</strong> for{' '}
              <strong>all environments</strong>. You should ensure that you do
              not contain any references to this segment in your applications
              before proceeding.
            </p>
            <InputGroup
              className='mb-0'
              inputProps={{
                className: 'full-width',
                name: 'confirm-segment-name',
              }}
              title='Please type the segment name to confirm'
              placeholder='segment_name'
              onChange={(e: InputEvent) => {
                setChallenge(Utils.safeParseEventValue(e))
              }}
            />
          </div>
          <ModalHR />
          <div className='modal-footer'>
            <Button className='mr-2' onClick={closeModal} theme='secondary'>
              Cancel
            </Button>
            <Button
              id='confirm-remove-segment-btn'
              disabled={challenge != segment.name}
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

export default ConfirmRemoveSegment
