import React, { FC, FormEvent, useState } from 'react'
import { Environment, Segment, SegmentCohort } from 'common/types/responses'
import ProjectProvider from 'common/providers/ProjectProvider'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import Button from 'components/base/forms/Button'
import ModalHR from './ModalHR'
import { deleteSegment } from 'common/services/useSegment'
import { deleteCohort } from 'common/services/useCohort'
import { getEnvironments } from 'common/services/useEnvironment'
import { getStore } from 'common/store'

type ConfirmRemoveSegmentType = {
  segment: Segment
  cb: () => void
}
export const handleRemoveSegment = (
  projectId: string,
  segment: Segment,
  onComplete?: () => void,
) => {
  // Cohort-managed segments must be deleted via their cohort; the segment
  // endpoint rejects them.
  const removeCohort = async (cohort: SegmentCohort) => {
    const { data: environments } = await getEnvironments(getStore(), {
      projectId: Number(projectId),
    })
    const environmentApiKey = environments?.results?.find(
      (environment: Environment) => environment.id === cohort.environment,
    )?.api_key
    if (!environmentApiKey) {
      throw new Error('Cohort environment not found')
    }
    return deleteCohort(getStore(), {
      cohortId: cohort.id,
      environmentApiKey,
      projectId: Number(projectId),
    })
  }
  const removeSegmentCallback = async () => {
    try {
      const res = segment.cohort
        ? await removeCohort(segment.cohort)
        : await deleteSegment(getStore(), { id: segment.id, projectId })
      if (res.error) throw new Error(res.error)
      toast(
        <div>
          Removed Segment: <strong>{segment.name}</strong>
        </div>,
      )
      onComplete?.()
    } catch (error) {
      toast(
        <div>
          Error removing segment: <strong>{segment.name}</strong>
        </div>,
        'danger',
      )
    }
  }
  openModal(
    'Remove Segment',
    <ConfirmRemoveSegment segment={segment} cb={removeSegmentCallback} />,
    'p-0',
  )
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
