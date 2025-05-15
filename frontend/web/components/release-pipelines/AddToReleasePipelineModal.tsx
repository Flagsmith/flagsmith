import { useEffect, useState } from 'react'
import {
  useAddFeatureToReleasePipelineMutation,
  useGetReleasePipelinesQuery,
} from 'common/services/useReleasePipelines'
import { ReleasePipeline } from 'common/types/responses'
import Utils from 'common/utils/utils'
import Button from 'components/base/forms/Button'
import InputGroup from 'components/base/forms/InputGroup'
import AccountStore from 'common/stores/account-store'

type AddToReleasePipelineModalProps = {
  projectId: string
  featureName: string
  featureId: number
}

const AddToReleasePipelineModal = ({
  featureId,
  featureName,
  projectId,
}: AddToReleasePipelineModalProps) => {
  const [selectedReleasePipeline, setSelectedReleasePipeline] =
    useState<string>('')
  const { data: releasePipelines } = useGetReleasePipelinesQuery({
    page: 1,
    page_size: 100,
    projectId: Number(projectId),
  })

  const [
    addFeatureToReleasePipeline,
    { error, isError, isLoading, isSuccess },
  ] = useAddFeatureToReleasePipelineMutation()

  const releasePipelinesOptions = releasePipelines?.results?.map(
    (pipeline: ReleasePipeline) => ({
      label: pipeline.name,
      value: pipeline.id,
    }),
  )

  const handleSelect = (option: { label: string; value: string }) => {
    setSelectedReleasePipeline(option.value)
  }

  const handleAddToReleasePipeline = () => {
    const data = {
      featureId: Number(featureId),
      pipelineId: Number(selectedReleasePipeline),
      projectId: Number(projectId),
    }
    addFeatureToReleasePipeline(data)
  }

  useEffect(() => {
    if (isSuccess) {
      closeModal2()
      toast('Feature added to release pipeline')
      return
    }

    if (isError) {
      toast(
        error?.data?.detail ?? 'Error adding feature to release pipeline',
        'danger',
      )
      return
    }
  }, [isSuccess, isError, error])

  return (
    <div className='p-4'>
      <InputGroup
        title='Release Pipeline'
        component={
          <Select
            options={releasePipelinesOptions}
            onChange={handleSelect}
            value={Utils.toSelectedValue(
              selectedReleasePipeline,
              releasePipelinesOptions,
              { label: 'Select Release Pipeline', value: '' },
            )}
          />
        }
      />
      <div className='text-right mt-4'>
        <Button
          theme='secondary'
          className='mr-2'
          onClick={() => closeModal2()}
        >
          Cancel
        </Button>
        <Button onClick={handleAddToReleasePipeline} disabled={isLoading}>
          Add to Release Pipeline
        </Button>
      </div>
    </div>
  )
}

export type { AddToReleasePipelineModalProps }
export default AddToReleasePipelineModal
