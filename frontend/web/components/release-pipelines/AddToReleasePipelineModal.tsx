import { useEffect, useMemo, useState } from 'react'
import {
  useAddFeatureToReleasePipelineMutation,
  useGetReleasePipelinesQuery,
} from 'common/services/useReleasePipelines'
import { ReleasePipeline } from 'common/types/responses'
import Utils from 'common/utils/utils'
import Button from 'components/base/forms/Button'
import SelectField from 'components/base/forms/SelectField'

type AddToReleasePipelineModalProps = {
  projectId: number
  featureId: number
}

const AddToReleasePipelineModal = ({
  featureId,
  projectId,
}: AddToReleasePipelineModalProps) => {
  const [selectedReleasePipeline, setSelectedReleasePipeline] = useState<
    number | null
  >(null)
  const { data: releasePipelines } = useGetReleasePipelinesQuery({
    order_by: '-created_at',
    page: 1,
    page_size: 100,
    projectId,
  })

  const [
    addFeatureToReleasePipeline,
    { error, isError, isLoading, isSuccess },
  ] = useAddFeatureToReleasePipelineMutation()

  const releasePipelinesOptions = useMemo(
    () =>
      releasePipelines?.results
        ?.filter((pipeline) => !!pipeline.published_by)
        ?.map((pipeline: ReleasePipeline) => ({
          label: pipeline.name,
          value: pipeline.id,
        })),
    [releasePipelines],
  )

  const handleSelect = (option: { label: string; value: number } | null) => {
    setSelectedReleasePipeline(option?.value ?? null)
  }

  const handleAddToReleasePipeline = () => {
    const data = {
      featureId: Number(featureId),
      pipelineId: Number(selectedReleasePipeline),
      projectId,
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
      <SelectField
        title='Release Pipeline'
        options={releasePipelinesOptions}
        onChange={handleSelect}
        placeholder='Select Release Pipeline'
        value={
          Utils.toSelectedValue(
            selectedReleasePipeline,
            releasePipelinesOptions,
          ) ?? null
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

export default AddToReleasePipelineModal
