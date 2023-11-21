import React, { FC, useEffect, useState } from 'react'
import ChipInput from 'components/ChipInput'
import ErrorMessage from 'components/ErrorMessage'
import Button from 'components/base/forms/Button'
import { useCreateIdentitiesMutation } from 'common/services/useIdentity' // we need this to make JSX compile
import Utils from 'common/utils/utils'

type CreateUserType = {
  environmentId: string
}

const CreateUser: FC<CreateUserType> = ({ environmentId }) => {
  const [value, setValue] = useState<string[]>([])
  const [createIdentities, { isError, isSuccess }] =
    useCreateIdentitiesMutation()
  const submit = () => {
    createIdentities({
      environmentId,
      identifiers: value,
      isEdge: Utils.getIsEdge(),
    })
  }
  useEffect(() => {
    if (isSuccess) {
      closeModal()
    }
  }, [isSuccess])
  return (
    <div>
      <div className='modal-body px-4'>
        <div className='fw-bold text-dark mt-4 mb-3'>
          Enter a comma or space separate list of user IDs.
        </div>
        <label>User IDs</label>
        <FormGroup className='text-right'>
          <ChipInput
            placeholder='User1, User2, User3'
            onChange={(value) => setValue(value)}
            value={value}
          />
        </FormGroup>
        {isError && (
          <ErrorMessage error='Some Identities already exist and were not created' />
        )}
        <div className='text-right mt-5'>
          <Button onClick={submit} disabled={!value?.length}>
            Create users
          </Button>
        </div>
      </div>
    </div>
  )
}

export default CreateUser

module.exports = CreateUser
