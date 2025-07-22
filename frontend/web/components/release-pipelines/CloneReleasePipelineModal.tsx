import { useEffect, useState } from 'react'
import { useCloneReleasePipelineMutation } from 'common/services/useReleasePipelines'
import Utils from 'common/utils/utils'
import Button from 'components/base/forms/Button'
import InputGroup from 'components/base/forms/InputGroup'

type CloneReleasePipelineModalProps = {
  projectId: number
  pipelineId: number
}

const CloneReleasePipelineModal = ({
  pipelineId,
  projectId,
}: CloneReleasePipelineModalProps) => {
  const [name, setName] = useState<string>('')

  const [
    cloneReleasePipeline,
    {
      error: cloneReleasePipelineError,
      isError: isCloningError,
      isLoading: isCloning,
      isSuccess: isCloningSuccess,
    },
  ] = useCloneReleasePipelineMutation()

  useEffect(() => {
    if (isCloningSuccess) {
      closeModal2()
      toast('Release pipeline cloned successfully')
      return
    }

    if (isCloningError) {
      toast(
        cloneReleasePipelineError?.data?.detail ??
          'Error cloning release pipeline',
        'danger',
      )
      return
    }
  }, [isCloningSuccess, isCloningError, cloneReleasePipelineError])

  return (
    <div className='p-4'>
      {/* <p>Add a name for the cloned release pipeline.</p> */}
      <InputGroup
        title='New Release Pipeline Name'
        inputProps={{
          className: 'full-width',
          error: !name,
          name: 'name',
        }}
        value={name}
        onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
          setName(Utils.safeParseEventValue(event))
        }}
        isValid={name && name.length}
        type='text'
        name='name'
        id='name'
        placeholder='E.g. Beta Release'
      />
      <div className='text-right mt-4'>
        <Button
          theme='secondary'
          className='mr-2'
          onClick={() => closeModal2()}
        >
          Cancel
        </Button>
        <Button
          onClick={() => cloneReleasePipeline({ name, pipelineId, projectId })}
          disabled={isCloning || !name}
        >
          Clone
        </Button>
      </div>
    </div>
  )
}

export type { CloneReleasePipelineModalProps }
export default CloneReleasePipelineModal
