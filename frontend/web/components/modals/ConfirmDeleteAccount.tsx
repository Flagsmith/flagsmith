import React, { FC, useEffect, useState } from 'react'
import ErrorMessage from 'components/ErrorMessage'
import Button from 'components/base/forms/Button'
import Utils from 'common/utils/utils'

type ConfirmDeleteAccountType = {
  userId: number
}

const ConfirmDeleteAccount: FC<ConfirmDeleteAccountType> = () => {
  const [password, setPassword] = useState<string>('')
  return (
    <div>
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
      {/*isError && (
        <ErrorMessage error=''/>
      )*/}
      <FormGroup className='text-right'>
        <Button>Delete</Button>
      </FormGroup>
    </div>
  )
}

export default ConfirmDeleteAccount

module.exports = ConfirmDeleteAccount
