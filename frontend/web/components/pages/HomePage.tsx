import React, { ChangeEvent, MouseEvent, useEffect, useState } from 'react'
import { useHistory, useLocation, withRouter } from 'react-router-dom'
import { GoogleOAuthProvider } from '@react-oauth/google'
import ForgotPasswordModal from 'components/modals/ForgotPasswordModal'
import Card from 'components/Card'
import NavIconSmall from 'components/svg/NavIconSmall'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
import ErrorMessage from 'components/ErrorMessage'
import Button from 'components/base/forms/Button'
import PasswordRequirements from 'components/PasswordRequirements'
import { informationCircleOutline } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'
import classNames from 'classnames'
import InfoMessage from 'components/InfoMessage'
import OnboardingPage from './OnboardingPage'
import isFreeEmailDomain from 'common/utils/isFreeEmailDomain'
import InputGroup from 'components/base/forms/InputGroup'
import { Link } from 'react-router-dom'
import Project from 'common/project'
import API from 'project/api'
import Utils from 'common/utils/utils'
// @ts-ignore
import data from 'common/data/base/_data'
import AppActions from 'common/dispatcher/app-actions'
import GoogleButton from 'components/GoogleButton'
import SamlForm from 'components/SamlForm'
import AccountProvider from 'common/providers/AccountProvider'
import AccountStore from 'common/stores/account-store'
import { LoginRequest, RegisterRequest } from 'common/types/requests'
import { useGetBuildVersionQuery } from 'common/services/useBuildVersion'
import { useUTMs } from 'common/useUTMs'

const HomePage: React.FC = () => {
  const history = useHistory()
  const location = useLocation()
  const [allRequirementsMet, setAllRequirementsMet] = useState(false)
  const [email, setEmail] = useState('')
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [marketingConsentGiven] = useState(true)
  const [password, setPassword] = useState('')

  const [samlError, setLocalError] = useState(false)
  const [samlLoading, setSamlLoading] = useState(false)
  const utms = useUTMs()
  const { data: version, isLoading: versionLoading } = useGetBuildVersionQuery(
    {},
  )

  // Note that we are explicitly setting marketing consent to true
  // here to reduce the complexity of the change. This is due to
  // the addition of wording in our ToS and the move from Pipedrive
  // to Hubspot.
  // TODO: this can probably all be removed from the FE and the BE
  // can handle always setting the marketing consent.
  useEffect(() => {
    API.setCookie('marketing_consent_given', 'true')
  }, [])

  const addAlbacross = () => {
    // @ts-ignore
    window._nQc = Project.albacross
    const script = document.createElement('script')
    script.type = 'text/javascript'
    script.async = true
    script.src = 'https://serve.albacross.com/track.js'
    script.id = 'albacross'
    document.body.appendChild(script)
  }

  useEffect(() => {
    const emailField = (document.querySelector('input[name="firstName"]') ||
      document.querySelector('input[name="email"]')) as HTMLInputElement
    emailField?.focus()

    if (Project.albacross && location.pathname.indexOf('signup') !== -1) {
      addAlbacross()
    }
  }, [location.pathname])

  useEffect(() => {
    const params = Utils.fromParam()
    const plan = params.plan
    if (plan) {
      API.setCookie('plan', plan)
    }
    if (Project.albacross && location.pathname.indexOf('signup') !== -1) {
      addAlbacross()
    }

    document.body.classList.remove('dark')

    if (document.location.href.includes('oauth')) {
      const parts = document.location.href.split('oauth/')
      const oauthParams = parts[1]
      if (oauthParams && oauthParams.includes('google')) {
        const access_token = params.code
        AppActions.oauthLogin('google', {
          access_token,
          marketing_consent_given: marketingConsentGiven,
        })
      } else if (oauthParams && oauthParams.includes('github')) {
        const access_token = params.code
        AppActions.oauthLogin('github', {
          access_token,
          marketing_consent_given: marketingConsentGiven,
        })
      }
    }

    setTimeout(() => {
      const emailField = (document.querySelector('input[name="firstName"]') ||
        document.querySelector('input[name="email"]')) as HTMLInputElement
      emailField?.focus()
    }, 1000)

    if (document.location.href.includes('saml')) {
      const access_token = params.code
      if (access_token) {
        AppActions.oauthLogin('saml', {
          access_token,
          marketing_consent_given: marketingConsentGiven,
        })
        history.replace('/')
      }
    }

    API.trackPage(Constants.pages.HOME)

    if (document.location.href.indexOf('invite') !== -1) {
      const invite = params.redirect
      if (invite.includes('invite-link')) {
        const id = invite.split('invite-link/')[1]
        API.setInviteType('INVITE_LINK')
        API.setInvite(id)
      } else if (invite.includes('invite')) {
        const id = invite.split('invite/')[1]
        API.setInviteType('INVITE_EMAIL')
        API.setInvite(id)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const handleRequirementsMet = (met: boolean) => {
    setAllRequirementsMet(met)
  }

  const showForgotPassword = (e: MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault()
    openModal(
      'Forgot password',
      <ForgotPasswordModal
        initialValue={email}
        onComplete={() => {
          toast('Please check your email to reset your password.')
        }}
      />,
      'p-0 modal-sm',
    )
  }

  const redirect = Utils.fromParam().redirect
    ? `?redirect=${Utils.fromParam().redirect}`
    : ''
  const currentLocation = `${document.location.pathname}${
    document.location.search || ''
  }`
  const isInvite = currentLocation.indexOf('invite') !== -1
  const preventSignup = Project.preventSignup && !isInvite
  const isSignup =
    !preventSignup &&
    ((isInvite && currentLocation.indexOf('login') === -1) ||
      currentLocation.indexOf('signup') !== -1)
  const disableSignup = preventSignup && isSignup
  const preventEmailPassword = Project.preventEmailPassword
  const disableForgotPassword = Project.preventForgotPassword
  const oauths: React.ReactNode[] = []
  const disableOauthRegister = Utils.getFlagsmithHasFeature(
    'disable_oauth_registration',
  )
  const oauthClasses = 'col-12 col-xl-4'
  const onboarding =
    !versionLoading && version?.backend?.self_hosted_data?.has_users === false
  if (onboarding) {
    return <OnboardingPage />
  }

  if (versionLoading) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  if ((!isSignup || !disableOauthRegister) && !disableSignup) {
    if (Utils.getFlagsmithValue('oauth_github')) {
      oauths.push(
        <div className={oauthClasses} key='github'>
          <Button
            theme='secondary'
            className='w-100'
            iconLeft='github'
            href={JSON.parse(Utils.getFlagsmithValue('oauth_github')).url}
          >
            GitHub
          </Button>
        </div>,
      )
    }

    if (Utils.getFlagsmithValue('oauth_google')) {
      oauths.push(
        <div className={oauthClasses} key='google'>
          <GoogleOAuthProvider
            clientId={
              JSON.parse(Utils.getFlagsmithValue('oauth_google')).clientId
            }
          >
            <GoogleButton
              className='w-100'
              onSuccess={(e) => {
                document.location.href = `${document.location.origin}/oauth/google?code=${e.access_token}`
              }}
            />
          </GoogleOAuthProvider>
        </div>,
      )
    }

    if (
      !Utils.flagsmithFeatureExists('saml') ||
      Utils.getFlagsmithHasFeature('saml')
    ) {
      oauths.push(
        <div className={oauthClasses}>
          <Button
            disabled={samlLoading}
            theme='secondary'
            onClick={() => {
              if (!Utils.getFlagsmithValue('sso_idp')) {
                openModal('Single Sign-On', <SamlForm />, 'p-0 modal-sm')
              } else {
                data
                  .post(
                    `${Project.api}auth/saml/${Utils.getFlagsmithValue(
                      'sso_idp',
                    )}/request/`,
                  )
                  .then((res: any) => {
                    if (res.headers && res.headers.Location) {
                      document.location.href = res.headers.Location
                    } else {
                      setLocalError(true)
                    }
                  })
                  .catch(() => {
                    setLocalError(true)
                    setSamlLoading(false)
                  })
              }
            }}
            className='w-100'
          >
            Single Sign-On
          </Button>
        </div>,
      )
    }
  }
  return (
    <AccountProvider>
      {(
        {
          error,
          isLoading,
          isSaving,
        }: { error?: any; isLoading: boolean; isSaving: boolean },
        {
          login,
          register,
        }: {
          register: (data: RegisterRequest, isInvite: boolean) => void
          login: (data: LoginRequest) => void
        },
      ) => (
        <div
          id='login-page'
          style={{ flexDirection: 'column' }}
          className='fullscreen-container bg-light200'
        >
          <div className='mb-4'>
            <NavIconSmall className='signup-icon' />
          </div>
          <div className='container mb-4'>
            {isSignup ? (
              <div className='text-center mb-4'>
                <h3>It's free to get started.</h3>
                {!isInvite && (
                  <>
                    <p className='mb-0'>
                      We have a 100% free for life plan for smaller projects.
                    </p>
                    <Button
                      theme='text'
                      className='pt-3 fw-bold'
                      href='https://flagsmith.com/pricing'
                      target='_blank'
                    >
                      Check out our Pricing
                    </Button>
                  </>
                )}
              </div>
            ) : (
              <div className='text-center mb-4'>
                <h3>Sign in to Flagsmith</h3>
                {!!oauths.length && (
                  <p>Log in to your account with one of these services.</p>
                )}
              </div>
            )}
            <div className='row'>
              <div className='col-md-6 offset-md-3'>
                {disableSignup ? (
                  <div id='sign-up'>
                    <Card>
                      To join an organisation please contact your administrator
                      for an invite link.
                      <div>
                        <Link id='existing-member-btn' to={`/login${redirect}`}>
                          <Button theme='text' className='mt-2 pb-3 pt-2'>
                            Already a member?
                          </Button>
                        </Link>
                      </div>
                    </Card>
                  </div>
                ) : (
                  <div id='sign-up'>
                    {!isSignup ? (
                      <>
                        <Card
                          className='mb-3'
                          contentClassName={classNames(
                            'd-flex flex-column gap-3',
                            { 'bg-light200': preventEmailPassword },
                          )}
                        >
                          <>
                            {!!oauths.length && (
                              <div className='d-flex flex-column flex-xl-row justify-content-center gap-2'>
                                {oauths}
                              </div>
                            )}
                            {!preventEmailPassword && (
                              <form
                                id='form'
                                name='form'
                                onSubmit={(e) => {
                                  e.preventDefault()
                                  login({ email, password })
                                }}
                              >
                                {isInvite && (
                                  <div className='notification flex-row'>
                                    <span className='notification__icon mb-2'>
                                      <IonIcon
                                        icon={informationCircleOutline}
                                      />
                                    </span>
                                    <p className='notification__text pl-3'>
                                      Log in to accept your invite
                                    </p>
                                  </div>
                                )}
                                <fieldset id='details'>
                                  <InputGroup
                                    title='Email Address / Username'
                                    data-test='email'
                                    inputProps={{
                                      className: 'full-width',
                                      error: error?.email,
                                      name: 'email',
                                    }}
                                    onChange={(
                                      e: ChangeEvent<HTMLInputElement>,
                                    ) => setEmail(Utils.safeParseEventValue(e))}
                                    className='input-default full-width mb-4'
                                    type='text'
                                    name='email'
                                    id='email'
                                  />
                                  <InputGroup
                                    title='Password'
                                    inputProps={{
                                      className: 'full-width',
                                      enableAutoComplete: true,
                                      error: error?.password,
                                      name: 'password',
                                    }}
                                    onChange={(
                                      e: ChangeEvent<HTMLInputElement>,
                                    ) =>
                                      setPassword(Utils.safeParseEventValue(e))
                                    }
                                    rightComponent={
                                      !disableForgotPassword && (
                                        <Link
                                          tabIndex={-1}
                                          className='float-right'
                                          to={`/password-recovery${redirect}`}
                                          onClick={showForgotPassword}
                                        >
                                          <Button
                                            theme='text'
                                            tabIndex={-1}
                                            type='button'
                                            className='fs-small'
                                          >
                                            Forgot password
                                          </Button>
                                        </Link>
                                      )
                                    }
                                    className='input-default full-width mb-2'
                                    type='password'
                                    name='password'
                                    data-test='password'
                                    id='password'
                                  />
                                  <div className='form-cta'>
                                    <Button
                                      id='login-btn'
                                      disabled={isLoading || isSaving}
                                      type='submit'
                                      className='mt-3 px-4 full-width'
                                    >
                                      Log in
                                    </Button>
                                  </div>
                                </fieldset>
                                {(AccountStore.error || samlError) && (
                                  <div
                                    id='error-alert'
                                    className='mt-3 font-weight-medium'
                                  >
                                    <ErrorMessage
                                      error={
                                        typeof AccountStore.error === 'string'
                                          ? AccountStore.error
                                          : 'Please check your details and try again'
                                      }
                                    />
                                  </div>
                                )}
                              </form>
                            )}
                          </>
                        </Card>
                        {!preventSignup && (
                          <div>
                            {!preventEmailPassword && (
                              <Row className='justify-content-center'>
                                Creating a new account is easy{' '}
                                <Link
                                  id='existing-member-btn'
                                  to={`/signup${redirect}`}
                                >
                                  <Button
                                    theme='text'
                                    data-test='jsSignup'
                                    className='ml-1 fw-bold'
                                  >
                                    Sign up
                                  </Button>
                                </Link>
                              </Row>
                            )}
                          </div>
                        )}
                      </>
                    ) : (
                      <>
                        <Card
                          className='mb-3'
                          contentClassName={classNames(
                            'd-flex flex-column gap-3',
                            { 'bg-light200': preventEmailPassword },
                          )}
                        >
                          {!!oauths.length && (
                            <div className='row row-gap-2'>{oauths}</div>
                          )}
                          {!preventEmailPassword && (
                            <form
                              id='form'
                              name='form'
                              onSubmit={(e) => {
                                e.preventDefault()
                                const isInvite =
                                  document.location.href.indexOf('invite') !==
                                  -1
                                register(
                                  {
                                    email,
                                    first_name: firstName,
                                    last_name: lastName,
                                    marketing_consent_given:
                                      marketingConsentGiven,
                                    password,
                                    ...utms,
                                  },
                                  isInvite,
                                )
                              }}
                            >
                              {error && (
                                <Row>
                                  <div
                                    id='error-alert'
                                    className='font-weight-medium'
                                  >
                                    <ErrorMessage
                                      error={
                                        typeof AccountStore.error?.detail ===
                                        'string'
                                          ? AccountStore.error.detail
                                          : 'Please check your details and try again'
                                      }
                                    />
                                  </div>
                                </Row>
                              )}
                              {isInvite && (
                                <div>
                                  <div className='notification flex-row'>
                                    <span className='notification__icon mb-2'>
                                      <IonIcon
                                        icon={informationCircleOutline}
                                      />
                                    </span>
                                    <p className='notification__text pl-3'>
                                      Create an account to accept your invite
                                    </p>
                                  </div>
                                  <Row className='justify-content-center'>
                                    Have an account?{' '}
                                    <Button
                                      theme='text'
                                      className='ml-1 fw-bold'
                                      onClick={() => {
                                        window.location.href = `/login${redirect}`
                                      }}
                                    >
                                      Log in
                                    </Button>
                                  </Row>
                                </div>
                              )}
                              <fieldset id='details'>
                                <InputGroup
                                  title='First Name'
                                  data-test='firstName'
                                  inputProps={{
                                    className: 'full-width',
                                    error: error && error.first_name,
                                    name: 'firstName',
                                  }}
                                  onChange={(
                                    e: ChangeEvent<HTMLInputElement>,
                                  ) =>
                                    setFirstName(Utils.safeParseEventValue(e))
                                  }
                                  className='input-default full-width'
                                  type='text'
                                  name='firstName'
                                  id='firstName'
                                />
                                <InputGroup
                                  title='Last Name'
                                  data-test='lastName'
                                  inputProps={{
                                    className: 'full-width',
                                    error: error && error.last_name,
                                    name: 'lastName',
                                  }}
                                  onChange={(
                                    e: ChangeEvent<HTMLInputElement>,
                                  ) =>
                                    setLastName(Utils.safeParseEventValue(e))
                                  }
                                  className='input-default full-width'
                                  type='text'
                                  name='lastName'
                                  id='lastName'
                                />
                                <InputGroup
                                  title='Email Address'
                                  data-test='email'
                                  inputProps={{
                                    className: 'full-width',
                                    enableAutoComplete: true,
                                    error: error && error.email,
                                    name: 'email',
                                  }}
                                  onChange={(
                                    e: ChangeEvent<HTMLInputElement>,
                                  ) => setEmail(Utils.safeParseEventValue(e))}
                                  className='input-default full-width'
                                  type='email'
                                  name='email'
                                  id='email'
                                />
                                {isFreeEmailDomain(email) && (
                                  <InfoMessage>
                                    Signing up with a work email makes it easier
                                    for co-workers to join your Flagsmith
                                    organisation.
                                  </InfoMessage>
                                )}
                                <InputGroup
                                  title='Password'
                                  data-test='password'
                                  inputProps={{
                                    className: 'full-width',
                                    error: error && error.password,
                                    name: 'password',
                                  }}
                                  onChange={(
                                    e: ChangeEvent<HTMLInputElement>,
                                  ) =>
                                    setPassword(Utils.safeParseEventValue(e))
                                  }
                                  className='input-default full-width'
                                  type='password'
                                  name='password'
                                  id='password'
                                />
                                <PasswordRequirements
                                  password={password}
                                  onRequirementsMet={handleRequirementsMet}
                                />
                                <div className='form-cta'>
                                  <Button
                                    data-test='signup-btn'
                                    name='signup-btn'
                                    disabled={
                                      isLoading ||
                                      isSaving ||
                                      !allRequirementsMet
                                    }
                                    className='px-4 mt-3 full-width'
                                    type='submit'
                                  >
                                    Create Account
                                  </Button>
                                </div>
                              </fieldset>
                            </form>
                          )}
                        </Card>
                      </>
                    )}
                  </div>
                )}
              </div>
              <div className='mt-4 text-center text-small text-muted'>
                By signing up you agree to our{' '}
                <a
                  style={{ opacity: 0.8 }}
                  target='_blank'
                  className='text-small'
                  href='https://flagsmith.com/terms-of-service/'
                  rel='noreferrer'
                >
                  Terms of Service
                </a>{' '}
                and{' '}
                <a
                  style={{ opacity: 0.8 }}
                  target='_blank'
                  className='text-small'
                  href='https://flagsmith.com/privacy-policy/'
                  rel='noreferrer'
                >
                  Privacy Policy
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </AccountProvider>
  )
}

export default ConfigProvider(withRouter(HomePage))
