import React, { ChangeEvent, FC, FormEvent, useEffect, useState } from 'react'
import { Link, useHistory, useParams } from 'react-router-dom'
import { FetchBaseQueryError } from '@reduxjs/toolkit/query'

import AccountStore from 'common/stores/account-store'
import Button from 'components/base/forms/Button'
import Card from 'components/Card'
import Constants from 'common/constants'
import ErrorMessage from 'components/ErrorMessage'
import InfoMessage from 'components/InfoMessage'
import InputGroup from 'components/base/forms/InputGroup'
import NavIconSmall from 'components/icons/NavIconSmall'
import Utils from 'common/utils/utils'
import API from 'project/api'
import {
  useActivateAccountMutation,
  useResendActivationEmailMutation,
} from 'common/services/useEmailActivation'

type ActivationParams = { uid: string; token: string }

const PageShell: FC<{ title: string; children: React.ReactNode }> = ({
  children,
  title,
}) => (
  <>
    <div className='text-center mb-4'>
      <h3>{title}</h3>
    </div>
    <div className='row'>
      <div className='col-md-6 offset-md-3'>
        <Card>{children}</Card>
      </div>
    </div>
  </>
)

const EmailActivationPage: FC = () => {
  const history = useHistory()
  const { token, uid } = useParams<ActivationParams>()

  const [email, setEmail] = useState('')

  const [activateAccount, { error: activationError, isError: hasFailed }] =
    useActivateAccountMutation()
  const [
    resendActivationEmail,
    { isError: hasResendFailed, isLoading: isResending, isSuccess: hasResent },
  ] = useResendActivationEmailMutation()

  // `isError` also covers network and 5xx failures, which are worth retrying.
  // Only the endpoint rejecting the token means the link is actually spent.
  const status = (activationError as FetchBaseQueryError | undefined)?.status
  const isLinkSpent = status === 400 || status === 403

  useEffect(() => {
    API.trackPage(Constants.pages.EMAIL_ACTIVATION, '/activate')
  }, [])

  useEffect(() => {
    activateAccount({ token, uid })
      .unwrap()
      .then(() => {
        AccountStore.pendingEmailVerification = null
        history.replace('/login', { isGettingStarted: true })
        toast('Your email has been verified, you can now log in')
      })
      .catch(() => {
        // Rendered as one of the failure states below.
      })
  }, [uid, token, history, activateAccount])

  const onResend = (e: FormEvent) => {
    e.preventDefault()
    resendActivationEmail({ email: email.toLowerCase() })
  }

  const backToSignIn = (
    <Link id='login-btn' to='/login'>
      <Button theme='text'>Back to sign in</Button>
    </Link>
  )

  const renderBody = () => {
    if (!hasFailed) {
      return (
        <div className='text-center'>
          <Loader />
          <p className='mt-3'>Verifying your email...</p>
        </div>
      )
    }

    if (!isLinkSpent) {
      return (
        <PageShell title='Something went wrong'>
          <p>
            We couldn't reach the server to verify your email. Your link is
            still valid.
          </p>
          <div className='d-flex gap-2 align-items-center'>
            <Button
              id='retry-activation-btn'
              onClick={() => activateAccount({ token, uid })}
            >
              Try again
            </Button>
            {backToSignIn}
          </div>
        </PageShell>
      )
    }

    return (
      <PageShell title='This link is no longer valid'>
        {hasResent ? (
          <InfoMessage>
            If that address needs verifying, we've sent a new link to it.
          </InfoMessage>
        ) : (
          <form onSubmit={onResend} id='resend-activation'>
            <p>
              Verification links expire, and can only be used once. Enter your
              email address and we'll send a new one.
            </p>
            <InputGroup
              inputProps={{ className: 'full-width', name: 'email' }}
              title='Email address'
              onChange={(e: ChangeEvent<HTMLInputElement>) => {
                setEmail(Utils.safeParseEventValue(e))
              }}
              className='input-default full-width'
              placeholder='you@example.com'
              type='email'
              id='email'
            />
            {hasResendFailed && (
              <ErrorMessage error='We could not send a new verification email. Please try again in a moment.' />
            )}
            <div className='d-flex gap-2 align-items-center'>
              <Button
                id='resend-verification-btn'
                type='submit'
                disabled={!email || isResending}
              >
                {isResending ? 'Sending...' : 'Send new link'}
              </Button>
              {backToSignIn}
            </div>
          </form>
        )}
      </PageShell>
    )
  }

  return (
    <div
      id='email-activation-page'
      style={{ flexDirection: 'column' }}
      className='fullscreen-container bg-light200'
    >
      <div className='mb-4'>
        <NavIconSmall className='signup-icon' />
      </div>
      <div className='container'>{renderBody()}</div>
    </div>
  )
}

export default EmailActivationPage
