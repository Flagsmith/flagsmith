import React, { FC, FormEvent, useState } from 'react'
import { Segment, SegmentRule } from 'common/types/responses'
import ProjectProvider from 'common/providers/ProjectProvider'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils' // we need this to make JSX compile
import Button from 'components/base/forms/Button'
import ModalHR from './ModalHR'

type CreateDuplicateSegmentType = {
  segment: Segment
  cb: (segment: Omit<Segment, 'id' | 'uuid'>) => void
}

const CreateDuplicateSegmentModal: FC<CreateDuplicateSegmentType> = ({
  cb,
  segment,
}) => {
  const [challenge, setChallenge] = useState()

  function removeIds(rules: SegmentRule[]): SegmentRule[] {
    return rules.map(rule => ({
      conditions: rule.conditions.map(({ delete: del, description, operator, property, value }) => ({
        delete: del,
        description,
        operator,
        property,
        value,
      })),
      delete: rule.delete,
      rules: removeIds(rule.rules),
      type: rule.type,
    }));
  }
  
  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (challenge) {
      const newSegment: Omit<Segment, 'id' | 'uuid'> = {
        description: segment.description,
        metadata: segment.metadata,
        name: challenge,
        project: segment.project,
        rules: removeIds(segment.rules),
        ...(segment.feature && { feature: segment.feature }),
      }
      closeModal()
      console.log(newSegment)
      cb(newSegment)
    }
  }

  return (
    <ProjectProvider>
      {() => (
        <form id='confirm-duplicate-segment-modal' onSubmit={submit}>
            <div className='modal-body'>
                <p>
                This will create a copy of <strong>{segment.name}</strong>, including all its rules and configuration.
                You can modify the duplicate without affecting the original segment.
                </p>
                <InputGroup
                className='mb-0'
                inputProps={{
                    className: 'full-width',
                    name: 'new-segment-name',
                }}
                title='Please enter a name for the new segment'
                placeholder='new_segment_name'
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
                id='confirm-duplicate-segment-btn'
                disabled={!challenge}
                type='submit'
                >
                Duplicate
                </Button>
            </div>
        </form>

      )}
    </ProjectProvider>
  )
}

export default CreateDuplicateSegmentModal
