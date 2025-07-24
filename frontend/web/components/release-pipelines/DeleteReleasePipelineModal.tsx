import { useEffect } from 'react'
import { useDeleteReleasePipelineMutation } from 'common/services/useReleasePipelines'
import Button from 'components/base/forms/Button'

type DeleteReleasePipelineModalProps = {
  projectId: number
  pipelineId: number
}

const DeleteReleasePipelineModal = ({
  pipelineId,
  projectId,
}: DeleteReleasePipelineModalProps) => {
  const [deleteReleasePipeline, { error, isError, isLoading, isSuccess }] =
    useDeleteReleasePipelineMutation()

  useEffect(() => {
    if (isSuccess) {
      closeModal2()
      toast('Release pipeline removed')
      return
    }

    if (isError) {
      toast('Error removing release pipeline', 'danger')
      return
    }
  }, [isSuccess, isError, error])

  const handleDeleteReleasePipeline = () => {
    deleteReleasePipeline({
      pipelineId,
      projectId,
    })
  }

  return (
    <div className='p-0'>
      <p>Are you sure you want to delete this release pipeline?</p>
      <div className='text-right mt-5'>
        <Button
          theme='secondary'
          className='mr-2'
          onClick={() => closeModal2()}
        >
          Cancel
        </Button>
        <Button onClick={handleDeleteReleasePipeline} disabled={isLoading}>
          Delete
        </Button>
      </div>
    </div>
  )
}

export type { DeleteReleasePipelineModalProps }
export default DeleteReleasePipelineModal
