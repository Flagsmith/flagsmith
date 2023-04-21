import React, { FC, useEffect, useState } from 'react'
import ErrorMessage from 'components/ErrorMessage'
import Button from 'components/base/forms/Button'
import Utils from 'common/utils/utils'
import { useDeleteDeleteUserAccountMutation } from 'common/services/useDeleteUserAccount'

type ConfirmDeleteAccountType = {
  userId: number
}

const ConfirmDeleteAccount: FC<ConfirmDeleteAccountType> = ({ userId }) => {
  const [password, setPassword] = useState<string>('')
  const [
    deleteUserAccount,
    {
      data: updateSegmentData,
      isError,
      isLoading: updating,
      isSuccess: updateSuccess,
    },
  ] = useDeleteDeleteUserAccountMutation()

  return (
    <div>
      <form
        onSubmit={(e) => {
          Utils.preventDefault(e)
          deleteUserAccount({
            current_password: password,
            id: userId,
          })
        }}
      >
        <FormGroup>
          <p>
            You will be removed from all organisations and all your account data
            will be deleted.
          </p>
          <label>Please re-enter your password for confirm this action.</label>
        </FormGroup>
        <InputGroup
          title='Password'
          inputProps={{
            className: 'full-width',
            name: 'currentPassword',
          }}
          value={password}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
            setPassword(Utils.safeParseEventValue(event))
          }}
          type='password'
          name='password'
        />
        {isError && (
          <div className='alert alert-danger'>
            Error deleting your account, please ensure you have entered your
            current password.
          </div>
        )}
        <FormGroup className='text-right'>
          <Button>Delete</Button>
        </FormGroup>
      </form>
    </div>
  )
}

export default ConfirmDeleteAccount

module.exports = ConfirmDeleteAccount
