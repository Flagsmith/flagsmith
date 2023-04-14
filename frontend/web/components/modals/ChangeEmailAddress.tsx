import React, { FC, useEffect, useState } from 'react'
import AccountProvider from 'common/providers/AccountProvider'
import ConfigProvider from 'common/providers/ConfigProvider'
import _data from 'common/data/base/_data'

type ChangeEmailAddressType = {}

const ChangeEmailAddress: FC<ChangeEmailAddressType> = () => {
  const [email, setEmail] = useState<string>('')
  const [password, setPassword] = useState<string>('')

  useEffect(() => {
    setTimeout(() => {
      document.getElementById('email')?.focus()
    }, 500)
  }, [])

  const close = () => {
    closeModal()
  }

  return (
    <AccountProvider onSave={close}>
      {({ error }) => (
        <form
          onSubmit={(e) => {
            Utils.preventDefault(e)
            //this.sendConfirmationEmail(yourEmail)
          }}
        >
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
            title='Re-enter Password'
            inputProps={{
              className: 'full-width',
              name: 'newPassword',
            }}
            value={password}
            onChange={(e) => {
              setPassword(e)
            }}
            type='password'
            name='password'
          />

          <div className='text-right'>
            <Button disabled={password.length === 0 && email.length === 0}>
              Save Changes
            </Button>
          </div>
        </form>
      )}
    </AccountProvider>
  )
}

export default ChangeEmailAddress

module.exports = ConfigProvider(ChangeEmailAddress)
