import React, { FC, FormEvent, useState } from 'react'
import { Segment } from 'common/types/responses'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils' // we need this to make JSX compile
import Button from 'components/base/forms/Button'
import ModalHR from './ModalHR'
import Format from 'common/utils/format'

type ConfirmCloneSegmentType = {
  cb: (name: string) => void
  isLoading?: boolean
  segment: Segment
}

const ConfirmCloneSegment: FC<ConfirmCloneSegmentType> = ({
  cb,
  isLoading,
  segment,
}) => {
  const [segmentCloneName, setSegmentCloneName] = useState('')

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (!!segmentCloneName && segmentCloneName !== segment.name) {
      closeModal()
      cb(segmentCloneName)
    }
  }

  return (
    <form id='confirm-clone-segment-modal' onSubmit={submit}>
      <div className='modal-body'>
        <InputGroup
          className='mb-0'
          inputProps={{
            className: 'full-width',
            name: 'confirm-segment-name',
          }}
          value={segmentCloneName}
          title='New Segment Name*'
          placeholder='E.g. power_users'
          onChange={(e: InputEvent) => {
            setSegmentCloneName(
              Format.enumeration
                .set(Utils.safeParseEventValue(e))
                .toLowerCase(),
            )
          }}
        />
      </div>
      <ModalHR />
      <div className='modal-footer'>
        <Button
          className='mr-2'
          onClick={closeModal}
          theme='secondary'
          disabled={isLoading}
        >
          Cancel
        </Button>
        <Button
          id='confirm-clone-segment-btn'
          disabled={!segmentCloneName || isLoading}
          type='submit'
        >
          Confirm
        </Button>
      </div>
    </form>
  )
}

export default ConfirmCloneSegment
