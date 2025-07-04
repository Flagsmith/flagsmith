import { useEffect, useState } from 'react'
import { useRemoveFeatureMutation } from 'common/services/useReleasePipelines'
import Button from 'components/base/forms/Button'

type RemoveFromReleasePipelineModalProps = {
  projectId: number
  featureId: number
  pipelineId: number
  onSuccess?: () => void
}

const RemoveFromReleasePipelineModal = ({
  featureId,
  onSuccess,
  pipelineId,
  projectId,
}: RemoveFromReleasePipelineModalProps) => {
  const [
    removeFeatureFromReleasePipeline,
    { error, isError, isLoading, isSuccess },
  ] = useRemoveFeatureMutation()

  useEffect(() => {
    if (isSuccess) {
      closeModal2()
      toast('Feature removed from release pipeline')
      onSuccess?.()
      return
    }

    if (isError) {
      toast('Error removing feature from release pipeline', 'danger')
      return
    }
  }, [isSuccess, isError, error, onSuccess])

  const handleRemoveFromReleasePipeline = () => {
    removeFeatureFromReleasePipeline({
      featureId,
      pipelineId,
      projectId,
    })
  }

  return (
    <div className='p-0'>
      <p>
        Removing this feature from the release pipeline{' '}
        <b>may affect pipeline actions that would apply to this feature.</b>
      </p>
      <div className='text-right mt-5'>
        <Button
          theme='secondary'
          className='mr-2'
          onClick={() => closeModal2()}
        >
          Cancel
        </Button>
        <Button onClick={handleRemoveFromReleasePipeline} disabled={isLoading}>
          Remove from Release Pipeline
        </Button>
      </div>
    </div>
  )
}

export type { RemoveFromReleasePipelineModalProps }
export default RemoveFromReleasePipelineModal
