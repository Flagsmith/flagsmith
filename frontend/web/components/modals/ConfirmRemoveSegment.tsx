import React, { FC, FormEvent, useState } from 'react'
import { Segment } from 'common/types/responses'
import ProjectProvider from 'common/providers/ProjectProvider'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils' // we need this to make JSX compile
import Button from 'components/base/forms/Button'

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
          <p>
            This will remove <strong>{segment.name}</strong> for{' '}
            <strong>all environments</strong>. You should ensure that you do not
            contain any references to this segment in your applications before
            proceeding.
          </p>
          <InputGroup
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

          <FormGroup className='text-right'>
            <Button
              id='confirm-remove-segment-btn'
              disabled={challenge != segment.name}
              type='submit'
            >
              Confirm changes
            </Button>
          </FormGroup>
        </form>
      )}
    </ProjectProvider>
  )
}

export default ConfirmRemoveSegment
