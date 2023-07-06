import React, { FC, useEffect, useState } from 'react'
import AccountProvider from 'common/providers/AccountProvider'
import ConfigProvider from 'common/providers/ConfigProvider'
import { useUpdateUserEmailMutation } from 'common/services/useUserEmail'
import Utils from 'common/utils/utils'
import InputGroup from 'components/base/forms/InputGroup'
import Button from 'components/base/forms/Button'
import ModalHR from './ModalHR'
import ErrorMessage from 'components/ErrorMessage'

type ChangeEmailAddressType = {
  onComplete?: () => void
}

const ChangeEmailAddress: FC<ChangeEmailAddressType> = ({ onComplete }) => {
  const [email, setEmail] = useState<string>('')
  const [password, setPassword] = useState<string>('')

  const [
    setUserEmail,
    {
      error: updateError,
      isError,
      isLoading: updating,
      isSuccess: updateSuccess,
    },
  ] = useUpdateUserEmailMutation()

  useEffect(() => {
    setTimeout(() => {
      document.getElementById('email')?.focus()
    }, 500)
  }, [])

  useEffect(() => {
    if (updateSuccess) {
      onComplete?.()
    }
    // eslint-disable-next-line
  }, [updateSuccess])

  const close = () => {
    closeModal()
  }

  return (
    <AccountProvider onSave={close}>
      {({ error }: { error?: Record<string, string> }) => (
        <form
          onSubmit={(e) => {
            Utils.preventDefault(e)
            setUserEmail({
              current_password: password,
              new_email: email,
            })
          }}
        >
          <div className='modal-body'>
            <InputGroup
              title='New Email Address'
              inputProps={{
                className: 'full-width',
                error: error && error.email,
                name: 'EmailAddress',
              }}
              value={email}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
                setEmail(Utils.safeParseEventValue(event))
              }}
              isValid={email && email.length}
              type='email'
              name='email'
              id='email'
              placeholder='E.g. email123@email.com'
            />
            <InputGroup
              title='Confirm Password'
              className='mb-0'
              inputProps={{
                className: 'full-width',
                name: 'newPassword',
              }}
              value={password}
              onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
                setPassword(Utils.safeParseEventValue(event))
              }}
              type='password'
              name='password'
            />
            {isError && (
              <ErrorMessage
                error={
                  updateError.data.current_password
                    ? updateError.data.current_password[0]
                    : 'An error occurred attempting to update your email address. Please verify that the email address you have provided is not already being used.'
                }
              />
            )}
          </div>
          <ModalHR />
          <div className='modal-footer'>
            <Button theme='secondary' className='mr-2' onClick={closeModal}>
              Cancel
            </Button>
            <Button
              type='submit'
              id='save-changes'
              data-tests='save-changes'
              disabled={
                updating || (password.length === 0 && email.length === 0)
              }
            >
              {updating ? 'Saving' : 'Save'}
            </Button>
          </div>
        </form>
      )}
    </AccountProvider>
  )
}

export default ChangeEmailAddress

module.exports = ConfigProvider(ChangeEmailAddress)
