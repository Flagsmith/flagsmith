import { useEffect } from 'react'
import {
  usePublishReleasePipelineMutation,
  useUnpublishReleasePipelineMutation,
} from 'common/services/useReleasePipelines'
import Button from 'components/base/forms/Button'

type ChangeReleasePipelineStatusModalProps = {
  projectId: number
  isPublished: boolean
  pipelineId: number
}

const ChangeReleasePipelineStatusModal = ({
  isPublished,
  pipelineId,
  projectId,
}: ChangeReleasePipelineStatusModalProps) => {
  const [
    publishReleasePipeline,
    {
      error: publishReleasePipelineError,
      isError: isPublishingError,
      isLoading: isPublishing,
      isSuccess: isPublishingSuccess,
    },
  ] = usePublishReleasePipelineMutation()

  const [
    unpublishReleasePipeline,
    {
      error: unpublishReleasePipelineError,
      isError: isUnpublishingError,
      isLoading: isUnpublishing,
      isSuccess: isUnpublishingSuccess,
    },
  ] = useUnpublishReleasePipelineMutation()

  useEffect(() => {
    if (isPublishingSuccess) {
      closeModal2()
      toast('Release pipeline published successfully')
      return
    }

    if (isPublishingError) {
      toast('Error publishing release pipeline', 'danger')
      return
    }
  }, [isPublishingSuccess, isPublishingError, publishReleasePipelineError])

  useEffect(() => {
    if (isUnpublishingSuccess) {
      closeModal2()
      toast('Release pipeline unpublished successfully')
      return
    }

    if (isUnpublishingError) {
      toast('Error unpublishing release pipeline', 'danger')
      return
    }
  }, [
    isUnpublishingSuccess,
    isUnpublishingError,
    unpublishReleasePipelineError,
  ])

  const handleConfirm = () => {
    if (isPublished) {
      unpublishReleasePipeline({
        pipelineId,
        projectId,
      })

      return
    }

    publishReleasePipeline({
      pipelineId,
      projectId,
    })
  }

  const isLoading = isPublishing || isUnpublishing

  return (
    <div className='p-0'>
      <p>
        Are you sure you want to{' '}
        <strong>{isPublished ? 'unpublish' : 'publish'}</strong> this release
        pipeline?
      </p>
      <div className='text-right mt-5'>
        <Button
          theme='secondary'
          className='mr-2'
          onClick={() => closeModal2()}
        >
          Cancel
        </Button>
        <Button onClick={handleConfirm} disabled={isLoading}>
          {isPublished ? 'Unpublish' : 'Publish'}
        </Button>
      </div>
    </div>
  )
}

export type { ChangeReleasePipelineStatusModalProps }
export default ChangeReleasePipelineStatusModal
