import React from 'react'
import { GoogleOAuthProvider } from '@react-oauth/google'
import ForgotPasswordModal from 'components/ForgotPasswordModal'
import Card from 'components/Card'
import { ButtonLink } from 'components/base/forms/Button'
import NavIconSmall from 'components/svg/NavIconSmall'
import SamlForm from 'components/SamlForm'
import data from 'common/data/base/_data'
import GoogleButton from 'components/GoogleButton'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'

const HomePage = class extends React.Component {
  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  static displayName = 'HomePage'

  constructor(props, context) {
    super(props, context)
    this.state = {
      marketing_consent_given:
        API.getCookie('marketing_consent_given') !== 'false',
    }
  }

  componentDidUpdate(prevProps) {
    if (this.props.location.pathname !== prevProps.location.pathname) {
      const emailField =
        document.querySelector('input[name="firstName"]') ||
        document.querySelector('input[name="email"]')
      if (emailField) {
        emailField.focus()
      }
    }
  }

  componentDidMount() {
    if (document.location.href.includes('oauth')) {
      const parts = location.href.split('oauth/')
      const params = parts[1]
      if (params && params.includes('google')) {
        const access_token = Utils.fromParam().code
        AppActions.oauthLogin('google', {
          access_token,
          marketing_consent_given: this.state.marketing_consent_given,
        })
      } else if (params && params.includes('github')) {
        const access_token = Utils.fromParam().code
        AppActions.oauthLogin('github', {
          access_token,
          marketing_consent_given: this.state.marketing_consent_given,
        })
      }
    }
    setTimeout(() => {
      const emailField =
        document.querySelector('input[name="firstName"]') ||
        document.querySelector('input[name="email"]')
      if (emailField) {
        emailField.focus()
      }
    }, 1000)

    if (document.location.href.includes('saml')) {
      const access_token = Utils.fromParam().code
      if (access_token) {
        AppActions.oauthLogin('saml', {
          access_token,
          marketing_consent_given: this.state.marketing_consent_given,
        })
        this.context.router.history.replace('/')
      }
    }
    API.trackPage(Constants.pages.HOME)

    if (document.location.href.indexOf('invite') !== -1) {
      const invite = Utils.fromParam().redirect

      if (invite.includes('invite-link')) {
        const id = invite.split('invite-link/')[1]
        API.setInviteType('INVITE_LINK')
        API.setInvite(id)
      } else if (invite.includes('invite')) {
        // persist invite incase user changes page or logs in with oauth
        const id = invite.split('invite/')[1]
        API.setInviteType('INVITE_EMAIL')
        API.setInvite(id)
      }
    }
  }

  showForgotPassword = (e) => {
    e.preventDefault()
    openModal(
      'Forgot password',
      <ForgotPasswordModal
        initialValue={this.state.email}
        onComplete={() => {
          toast('Please check your email to reset your password.')
        }}
      />,
      null,
      { className: 'alert fade expand' },
    )
  }

  render = () => {
    const { email, first_name, last_name, password } = this.state
    const redirect = Utils.fromParam().redirect
      ? `?redirect=${Utils.fromParam().redirect}`
      : ''
    const isInvite = document.location.href.indexOf('invite') !== -1
    const isSignup =
      !Project.preventSignup &&
      ((isInvite && document.location.href.indexOf('login') === -1) ||
        document.location.href.indexOf('signup') !== -1)
    const disableSignup = Project.preventSignup && isSignup
    const preventEmailPassword = Project.preventEmailPassword
    const disableForgotPassword = Project.preventForgotPassword
    const oauths = []
    const disableOauthRegister = Utils.getFlagsmithHasFeature(
      'disable_oauth_registration',
    )

    if ((!isSignup || !disableOauthRegister) && !disableSignup) {
      if (Utils.getFlagsmithValue('oauth_github')) {
        oauths.push(
          <a
            key='github'
            className='btn btn__oauth btn__oauth--github'
            href={JSON.parse(Utils.getFlagsmithValue('oauth_github')).url}
          >
            <svg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'>
              <path d='M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12' />
            </svg>{' '}
            GitHub
          </a>,
        )
      }

      if (Utils.getFlagsmithValue('oauth_google')) {
        oauths.push(
          <GoogleOAuthProvider
            clientId={
              JSON.parse(Utils.getFlagsmithValue('oauth_google')).clientId
            }
          >
            <GoogleButton
              onSuccess={(e) => {
                document.location = `${document.location.origin}/oauth/google?code=${e.access_token}`
              }}
            />
          </GoogleOAuthProvider>,
        )
      }

      if (Utils.getFlagsmithHasFeature('saml')) {
        oauths.push(
          <a
            onClick={() => {
              if (!Utils.getFlagsmithValue('sso_idp')) {
                openModal('Single Sign-On', <SamlForm />)
              } else {
                data
                  .post(
                    `${Project.api}auth/saml/${Utils.getFlagsmithValue(
                      'sso_idp',
                    )}/request/`,
                  )
                  .then((res) => {
                    if (res.headers && res.headers.Location) {
                      document.location.href = res.headers.Location
                    } else {
                      this.setState({ error: true })
                    }
                  })
                  .catch(() => {
                    this.setState({ error: true, isLoading: false })
                  })
              }
            }}
            key='single-sign-on'
            className='btn btn__oauth btn__oauth--saml'
          >
            Single Sign-On
          </a>,
        )
      }
    }

    return (
      <>
        <AccountProvider onLogout={this.onLogout} onLogin={this.onLogin}>
          {({ error, isLoading, isSaving }, { register }) => (
            <div
              id='login-page'
              style={{ flexDirection: 'column' }}
              className='fullscreen-container'
            >
              <div className='mb-4'>
                <NavIconSmall className='signup-icon' />
              </div>
              <div className='text-center mb-4'>
                {isSignup ? (
                  <>
                    <h3>It's free to get started.</h3>
                    {!isInvite && (
                      <>
                        <p className='mb-0'>
                          We have a 100% free for life plan for smaller
                          projects.
                        </p>
                        <ButtonLink
                          className='pt-3 pb-3'
                          href='https://flagsmith.com/pricing'
                          target='_blank'
                        >
                          Check out our Pricing
                        </ButtonLink>
                      </>
                    )}
                  </>
                ) : (
                  <>
                    <h3>Sign in to Flagsmith</h3>
                    {!!oauths.length && (
                      <p>Log in to your account with one of these services.</p>
                    )}
                  </>
                )}
              </div>

              {disableSignup && (
                <div className='signup-form' id='sign-up'>
                  <Card>
                    To join an organisation please contact your administrator
                    for an invite link.
                    <div>
                      <Link id='existing-member-btn' to={`/login${redirect}`}>
                        <ButtonLink className='mt-2 pb-3 pt-2'>
                          Already a member?
                        </ButtonLink>
                      </Link>
                    </div>
                  </Card>
                </div>
              )}

              {!disableSignup && (
                <div className='signup-form' id='sign-up'>
                  {!isSignup ? (
                    <React.Fragment>
                      <Card>
                        <AccountProvider>
                          {({ error, isLoading, isSaving }, { login }) => (
                            <>
                              {!!oauths.length && (
                                <Row style={{ justifyContent: 'center' }}>
                                  {oauths}
                                </Row>
                              )}
                              {!preventEmailPassword && (
                                <form
                                  id='form'
                                  name='form'
                                  onSubmit={(e) => {
                                    Utils.preventDefault(e)
                                    login({ email, password })
                                  }}
                                >
                                  {isInvite && (
                                    <div className='notification flex-row'>
                                      <span className='notification__icon ion-md-information-circle-outline mb-2' />
                                      <p className='notification__text pl-3'>
                                        Login to accept your invite
                                      </p>
                                    </div>
                                  )}
                                  <fieldset id='details'>
                                    {error && error.email ? (
                                      <span
                                        id='email-error'
                                        className='text-danger'
                                      >
                                        {error.email}
                                      </span>
                                    ) : null}
                                    <InputGroup
                                      title='Email Address / Username'
                                      data-test='email'
                                      inputProps={{
                                        className: 'full-width',
                                        error: error && error.email,
                                        name: 'email',
                                      }}
                                      onChange={(e) => {
                                        this.setState({
                                          email: Utils.safeParseEventValue(e),
                                        })
                                      }}
                                      className='input-default full-width mb-2 '
                                      type='text'
                                      name='email'
                                      id='email'
                                    />
                                    {error && error.password ? (
                                      <span
                                        id='password-error'
                                        className='text-danger'
                                      >
                                        {error.password}
                                      </span>
                                    ) : null}
                                    <InputGroup
                                      title='Password'
                                      inputProps={{
                                        className: 'full-width',
                                        error: error && error.password,
                                        name: 'password',
                                      }}
                                      onChange={(e) => {
                                        this.setState({
                                          password:
                                            Utils.safeParseEventValue(e),
                                        })
                                      }}
                                      rightComponent={
                                        !disableForgotPassword && (
                                          <Link
                                            tabIndex={-1}
                                            className='float-right'
                                            to={`/password-recovery${redirect}`}
                                            onClick={this.showForgotPassword}
                                          >
                                            <ButtonLink
                                              tabIndex={-1}
                                              type='button'
                                            >
                                              Forgot password?
                                            </ButtonLink>
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
                                        Login
                                      </Button>
                                    </div>
                                  </fieldset>
                                  {error && (
                                    <div
                                      id='error-alert'
                                      className='alert mt-3 alert-danger'
                                    >
                                      {typeof AccountStore.error === 'string'
                                        ? AccountStore.error
                                        : 'Please check your details and try again'}
                                    </div>
                                  )}
                                </form>
                              )}
                            </>
                          )}
                        </AccountProvider>
                      </Card>

                      {!Project.preventSignup && (
                        <div>
                          {!preventEmailPassword && (
                            <Row className='justify-content-center mt-2'>
                              Creating a new account is easy{' '}
                              <Link
                                id='existing-member-btn'
                                to={`/signup${redirect}`}
                              >
                                <ButtonLink
                                  data-test='jsSignup'
                                  className='ml-1'
                                >
                                  Sign up
                                </ButtonLink>
                              </Link>
                            </Row>
                          )}

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
                      )}
                    </React.Fragment>
                  ) : (
                    <React.Fragment>
                      <Card>
                        {!!oauths.length && (
                          <Row style={{ justifyContent: 'center' }}>
                            {oauths}
                          </Row>
                        )}

                        {!preventEmailPassword && (
                          <form
                            id='form'
                            name='form'
                            onSubmit={(e) => {
                              Utils.preventDefault(e)
                              const isInvite =
                                document.location.href.indexOf('invite') !== -1
                              register(
                                {
                                  email,
                                  first_name,
                                  last_name,
                                  marketing_consent_given:
                                    this.state.marketing_consent_given,
                                  password,
                                },
                                isInvite,
                              )
                            }}
                          >
                            {error && (
                              <FormGroup>
                                <div
                                  id='error-alert'
                                  className='alert alert-danger'
                                >
                                  {typeof AccountStore.error === 'string'
                                    ? AccountStore.error
                                    : 'Please check your details and try again'}
                                </div>
                              </FormGroup>
                            )}
                            {isInvite && (
                              <div className='notification flex-row'>
                                <span className='notification__icon ion-md-information-circle-outline mb-2' />
                                <p className='notification__text pl-3'>
                                  Create an account to accept your invite
                                </p>
                              </div>
                            )}
                            <fieldset id='details' className=''>
                              <InputGroup
                                title='First Name'
                                data-test='firstName'
                                inputProps={{
                                  className: 'full-width mb-2',
                                  error: error && error.first_name,
                                  name: 'firstName',
                                }}
                                onChange={(e) => {
                                  this.setState({
                                    first_name: Utils.safeParseEventValue(e),
                                  })
                                }}
                                className='input-default full-width'
                                type='text'
                                name='firstName'
                                id='firstName'
                              />
                              <InputGroup
                                title='Last Name'
                                data-test='lastName'
                                inputProps={{
                                  className: 'full-width mb-2',
                                  error: error && error.last_name,
                                  name: 'lastName',
                                }}
                                onChange={(e) => {
                                  this.setState({
                                    last_name: Utils.safeParseEventValue(e),
                                  })
                                }}
                                className='input-default full-width'
                                type='text'
                                name='lastName'
                                id='lastName'
                              />

                              {error && error.email ? (
                                <span id='email-error' className='text-danger'>
                                  {error.email}
                                </span>
                              ) : null}
                              <InputGroup
                                title='Email Address'
                                data-test='email'
                                inputProps={{
                                  className: 'full-width mb-2',
                                  error: error && error.email,
                                  name: 'email',
                                }}
                                onChange={(e) => {
                                  this.setState({
                                    email: Utils.safeParseEventValue(e),
                                  })
                                }}
                                className='input-default full-width'
                                type='email'
                                name='email'
                                id='email'
                              />

                              {error && error.password ? (
                                <span
                                  id='password-error'
                                  className='text-danger'
                                >
                                  {error.password}
                                </span>
                              ) : null}
                              <InputGroup
                                title='Password'
                                data-test='password'
                                inputProps={{
                                  className: 'full-width mb-2',
                                  error: error && error.password,
                                  name: 'password',
                                }}
                                onChange={(e) => {
                                  this.setState({
                                    password: Utils.safeParseEventValue(e),
                                  })
                                }}
                                className='input-default full-width'
                                type='password'
                                name='password'
                                id='password'
                              />
                              {Utils.getFlagsmithHasFeature('mailing_list') && (
                                <Row className='text-right'>
                                  <Flex />
                                  <input
                                    onChange={(e) => {
                                      API.setCookie(
                                        'marketing_consent_given',
                                        `${e.target.checked}`,
                                      )
                                      this.setState({
                                        marketing_consent_given:
                                          e.target.checked,
                                      })
                                    }}
                                    id='mailinglist'
                                    className='mr-2'
                                    type='checkbox'
                                    checked={this.state.marketing_consent_given}
                                  />
                                  <label className='mb-0' htmlFor='mailinglist'>
                                    Join our mailing list!
                                  </label>
                                </Row>
                              )}
                              <div className='form-cta'>
                                <Button
                                  data-test='signup-btn'
                                  name='signup-btn'
                                  disabled={isLoading || isSaving}
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
                      <Row className='justify-content-center mt-2'>
                        Have an account?{' '}
                        <Link id='existing-member-btn' to={`/login${redirect}`}>
                          <ButtonLink className='ml-1'>Log in</ButtonLink>
                        </Link>
                      </Row>
                    </React.Fragment>
                  )}
                </div>
              )}
            </div>
          )}
        </AccountProvider>
      </>
    )
  }
}

module.exports = ConfigProvider(HomePage)
