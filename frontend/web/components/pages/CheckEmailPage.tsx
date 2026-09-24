import React, { FC, useEffect } from 'react'
import { Link, useHistory, useLocation } from 'react-router-dom'

import AccountStore from 'common/stores/account-store'
import Button from 'components/base/forms/Button'
import Card from 'components/Card'
import Constants from 'common/constants'
import ErrorMessage from 'components/ErrorMessage'
import InfoMessage from 'components/InfoMessage'
import NavIconSmall from 'components/icons/NavIconSmall'
import API from 'project/api'
import { useResendActivationEmailMutation } from 'common/services/useEmailActivation'

type LocationState = { email?: string } | undefined

const CheckEmailPage: FC = () => {
  const history = useHistory()
  const location = useLocation<LocationState>()

  // Router state survives a reload of this page; the store does not.
  const email = (
    location.state?.email ||
    AccountStore.pendingEmailVerification ||
    ''
  ).toLowerCase()

  const [resendActivationEmail, { isError, isLoading, isSuccess }] =
    useResendActivationEmailMutation()

  useEffect(() => {
    API.trackPage(Constants.pages.CHECK_EMAIL)
  }, [])

  useEffect(() => {
    if (!email) {
      history.replace('/login')
    }
  }, [email, history])

  if (!email) {
    return null
  }

  return (
    <div
      id='check-email-page'
      style={{ flexDirection: 'column' }}
      className='fullscreen-container bg-light200'
    >
      <div className='mb-4'>
        <NavIconSmall className='signup-icon' />
      </div>
      <div className='container'>
        <div className='text-center mb-4'>
          <h3>Check your email</h3>
          <p className='mb-0'>
            We've sent a verification link to <strong>{email}</strong>.
          </p>
        </div>
        <div className='row'>
          <div className='col-md-6 offset-md-3'>
            <Card>
              <p>
                Click the link in that email to activate your account. You won't
                be able to log in until you do.
              </p>
              <p className='text-muted fs-small lh-sm mb-0'>
                Can't find it? Check your spam folder, and make sure{' '}
                <strong>{email}</strong> is correct.
              </p>

              {isSuccess && (
                <InfoMessage>
                  Verification email sent. It may take a minute to arrive.
                </InfoMessage>
              )}
              {isError && (
                <ErrorMessage error='We could not resend the verification email. Please try again in a moment.' />
              )}

              <div className='mt-4 d-flex gap-2 align-items-center'>
                <Button
                  id='resend-verification-btn'
                  onClick={() => resendActivationEmail({ email })}
                  disabled={isLoading}
                >
                  {isLoading ? 'Sending...' : 'Resend email'}
                </Button>
                <Link id='login-btn' to='/login'>
                  <Button theme='text'>Back to sign in</Button>
                </Link>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CheckEmailPage
