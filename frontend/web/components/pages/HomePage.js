import React from 'react'
import { GoogleOAuthProvider } from '@react-oauth/google'
import ForgotPasswordModal from 'components/modals/ForgotPasswordModal'
import Card from 'components/Card'
import NavIconSmall from 'components/svg/NavIconSmall'
import SamlForm from 'components/SamlForm'
import data from 'common/data/base/_data'
import GoogleButton from 'components/GoogleButton'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
import ErrorMessage from 'components/ErrorMessage'
import Button from 'components/base/forms/Button'
import { informationCircleOutline } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'
import Checkbox from 'components/base/forms/Checkbox'

const HomePage = class extends React.Component {
  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  static displayName = 'HomePage'

  constructor(props, context) {
    super(props, context)

    // Note that we are explicitly setting marketing consent to true
    // here to reduce the complexity of the change. This is due to
    // the addition of wording in our ToS and the move from Pipedrive
    // to Hubspot.
    // TODO: this can probably all be removed from the FE and the BE
    // can handle always setting the marketing consent.
    API.setCookie('marketing_consent_given', 'true')
    this.state = {
      marketing_consent_given: true,
    }
  }

  addAlbacross() {
    window._nQc = Project.albacross
    const script = document.createElement('script')
    script.type = 'text/javascript'
    script.async = true
    script.src = 'https://serve.albacross.com/track.js'
    script.id = 'albacross'

    document.body.appendChild(script)
  }

  componentDidUpdate(prevProps) {
    if (this.props.location.pathname !== prevProps.location.pathname) {
      const emailField =
        document.querySelector('input[name="firstName"]') ||
        document.querySelector('input[name="email"]')
      if (emailField) {
        emailField.focus()
      }
      if (
        Project.albacross &&
        this.props.location.pathname.indexOf('signup') !== -1
      ) {
        this.addAlbacross()
      }
    }
  }

  componentDidMount() {
    if (
      Project.albacross &&
      this.props.location.pathname.indexOf('signup') !== -1
    ) {
      this.addAlbacross()
    }

    document.body.classList.remove('dark')
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
      'p-0 modal-sm',
    )
  }

  render = () => {
    const { email, first_name, last_name, password } = this.state
    const redirect = Utils.fromParam().redirect
      ? `?redirect=${Utils.fromParam().redirect}`
      : ''
    const location = `${document.location.pathname}${
      document.location.search || ''
    }`
    const isInvite = location.indexOf('invite') !== -1
    const preventSignup = Project.preventSignup && !isInvite
    const isSignup =
      !preventSignup &&
      ((isInvite && location.indexOf('login') === -1) ||
        location.indexOf('signup') !== -1)
    const disableSignup = preventSignup && isSignup
    const preventEmailPassword = Project.preventEmailPassword
    const disableForgotPassword = Project.preventForgotPassword
    const oauths = []
    const disableOauthRegister = Utils.getFlagsmithHasFeature(
      'disable_oauth_registration',
    )
    const oauthClasses = 'col-12 col-md-4'

    if ((!isSignup || !disableOauthRegister) && !disableSignup) {
      if (Utils.getFlagsmithValue('oauth_github')) {
        oauths.push(
          <div className={oauthClasses}>
            <Button
              theme='secondary'
              className='full-width flex-row justify-content-center align-items-center'
              key='github'
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
          <div className={oauthClasses}>
            <GoogleOAuthProvider
              clientId={
                JSON.parse(Utils.getFlagsmithValue('oauth_google')).clientId
              }
            >
              <GoogleButton
                className='full-width flex-row justify-content-center align-items-center'
                onSuccess={(e) => {
                  document.location = `${document.location.origin}/oauth/google?code=${e.access_token}`
                }}
              />
            </GoogleOAuthProvider>
          </div>,
        )
      }

      if (Utils.getFlagsmithHasFeature('saml')) {
        oauths.push(
          <div className={oauthClasses}>
            <Button
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
            >
              Single Sign-On
            </Button>
          </div>,
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
                          We have a 100% free for life plan for smaller
                          projects.
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
                    {disableSignup && (
                      <div id='sign-up'>
                        <Card>
                          To join an organisation please contact your
                          administrator for an invite link.
                          <div>
                            <Link
                              id='existing-member-btn'
                              to={`/login${redirect}`}
                            >
                              <Button theme='text' className='mt-2 pb-3 pt-2'>
                                Already a member?
                              </Button>
                            </Link>
                          </div>
                        </Card>
                      </div>
                    )}

                    {!disableSignup && (
                      <div id='sign-up'>
                        {!isSignup ? (
                          <React.Fragment>
                            <Card className='mb-3'>
                              <AccountProvider>
                                {(
                                  { error, isLoading, isSaving },
                                  { login },
                                ) => (
                                  <>
                                    {!!oauths.length && (
                                      <div className='row mb-4'>{oauths}</div>
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
                                            <span className='notification__icon mb-2'>
                                              <IonIcon
                                                icon={informationCircleOutline}
                                              />
                                            </span>
                                            <p className='notification__text pl-3'>
                                              Login to accept your invite
                                            </p>
                                          </div>
                                        )}
                                        <fieldset id='details'>
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
                                                email:
                                                  Utils.safeParseEventValue(e),
                                              })
                                            }}
                                            className='input-default full-width mb-4'
                                            type='text'
                                            name='email'
                                            id='email'
                                          />
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
                                                  onClick={
                                                    this.showForgotPassword
                                                  }
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
                                              Login
                                            </Button>
                                          </div>
                                        </fieldset>
                                        {error && (
                                          <div
                                            id='error-alert'
                                            className='mt-3 font-weight-medium'
                                          >
                                            <ErrorMessage
                                              error={
                                                typeof AccountStore.error ===
                                                'string'
                                                  ? AccountStore.error
                                                  : 'Please check your details and try again'
                                              }
                                            />
                                          </div>
                                        )}
                                      </form>
                                    )}
                                  </>
                                )}
                              </AccountProvider>
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
                          </React.Fragment>
                        ) : (
                          <React.Fragment>
                            <Card className='mb-3'>
                              {!!oauths.length && (
                                <div className='row mb-4'>{oauths}</div>
                              )}

                              {!preventEmailPassword && (
                                <form
                                  id='form'
                                  name='form'
                                  onSubmit={(e) => {
                                    Utils.preventDefault(e)
                                    const isInvite =
                                      document.location.href.indexOf(
                                        'invite',
                                      ) !== -1
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
                                        className='font-weight-medium'
                                      >
                                        <ErrorMessage
                                          error={
                                            typeof AccountStore.error ===
                                            'string'
                                              ? AccountStore.error
                                              : 'Please check your details and try again'
                                          }
                                        />
                                      </div>
                                    </FormGroup>
                                  )}
                                  {isInvite && (
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
                                  )}
                                  <fieldset id='details' className=''>
                                    <InputGroup
                                      title='First Name'
                                      data-test='firstName'
                                      inputProps={{
                                        className: 'full-width',
                                        error: error && error.first_name,
                                        name: 'firstName',
                                      }}
                                      onChange={(e) => {
                                        this.setState({
                                          first_name:
                                            Utils.safeParseEventValue(e),
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
                                        className: 'full-width',
                                        error: error && error.last_name,
                                        name: 'lastName',
                                      }}
                                      onChange={(e) => {
                                        this.setState({
                                          last_name:
                                            Utils.safeParseEventValue(e),
                                        })
                                      }}
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
                                    <InputGroup
                                      title='Password'
                                      data-test='password'
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
                                      className='input-default full-width'
                                      type='password'
                                      name='password'
                                      id='password'
                                    />
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
                          </React.Fragment>
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
      </>
    )
  }
}

module.exports = ConfigProvider(HomePage)
