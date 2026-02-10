import React, { FC, useEffect, useState } from 'react'
import ErrorMessage from 'components/ErrorMessage'
import Button from 'components/base/forms/Button'
import Input from 'components/base/forms/Input'
import {
  useCreateBucketMutation,
  useUpdateBucketMutation,
} from 'common/services/useBucket'
import { Bucket } from 'common/types/responses'

type CreateBucketType = {
  projectId: number
  bucket?: Bucket
}

const CreateBucket: FC<CreateBucketType> = ({ bucket, projectId }) => {
  const [name, setName] = useState(bucket?.name || '')
  const [description, setDescription] = useState(bucket?.description || '')
  const [createBucket, { error: createError, isSuccess: createSuccess }] =
    useCreateBucketMutation()
  const [updateBucket, { error: updateError, isSuccess: updateSuccess }] =
    useUpdateBucketMutation()

  const isEdit = !!bucket
  const error = createError || updateError
  const isSuccess = createSuccess || updateSuccess

  const submit = () => {
    const body = { description, name }
    if (isEdit) {
      updateBucket({ body, id: bucket.id, projectId })
    } else {
      createBucket({ body, projectId })
    }
  }

  useEffect(() => {
    if (isSuccess) {
      closeModal()
      toast(
        isEdit ? 'Bucket updated successfully' : 'Bucket created successfully',
      )
    }
  }, [isSuccess, isEdit])

  const isValid = name.trim().length > 0

  return (
    <div>
      <div className='modal-body px-4'>
        <div className='fw-bold text-dark mt-4 mb-3'>
          {isEdit
            ? 'Edit bucket details'
            : 'Create a new bucket to organize your features'}
        </div>
        <FormGroup className='mb-4'>
          <label htmlFor='bucket-name'>Bucket Name *</label>
          <Input
            id='bucket-name'
            value={name}
            onChange={(e: any) => setName(e.target.value)}
            placeholder='e.g., Authentication Features'
            className='full-width'
          />
        </FormGroup>
        <FormGroup>
          <label htmlFor='bucket-description'>Description</label>
          <Input
            id='bucket-description'
            value={description}
            onChange={(e: any) => setDescription(e.target.value)}
            placeholder='Describe the purpose of this bucket'
            className='full-width'
            textarea
            rows={3}
          />
        </FormGroup>
        {error && (
          <ErrorMessage
            error={
              // @ts-ignore
              error?.data?.name?.[0] || 'Failed to save bucket. Please try again.'
            }
          />
        )}
        <div className='text-right mt-5'>
          <Button theme='secondary' onClick={closeModal} className='mr-2'>
            Cancel
          </Button>
          <Button onClick={submit} disabled={!isValid}>
            {isEdit ? 'Update Bucket' : 'Create Bucket'}
          </Button>
        </div>
      </div>
    </div>
  )
}

export default CreateBucket

module.exports = CreateBucket
