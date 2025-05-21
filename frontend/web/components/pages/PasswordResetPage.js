import React, { Component } from 'react'
import Constants from 'common/constants'
import ErrorMessage from 'components/ErrorMessage'

const PasswordResetPage = class extends Component {
  static displayName = 'PasswordResetPage'

  constructor(props, context) {
    super(props, context)
    this.state = {}
  }

  componentDidMount = () => {
    API.trackPage(Constants.pages.RESET_PASSWORD)
  }

  onSave = () => {
    this.props.history.replace('/login')
    toast('Your password has been reset')
  }

  save = (e) => {
    e.preventDefault()
    const isValid =
      this.state.password && this.state.password == this.state.password2
    if (isValid) {
      AppActions.resetPassword({
        new_password1: this.state.password,
        new_password2: this.state.password2,
        token: this.props.match.params.token,
        uid: this.props.match.params.uid,
      })
    }
  }

  render() {
    const isValid =
      this.state.password && this.state.password == this.state.password2
    return (
      <div className='app-container'>
        <AccountProvider onSave={this.onSave}>
          {({ error, isSaving }) => (
            <div className='card signup-form container px-4 py-4'>
              <h3>Reset Password</h3>

              {isSaving ? (
                <div className='centered-container'>
                  <Loader />
                </div>
              ) : (
                <form onSubmit={this.save} id='details'>
                  <InputGroup
                    inputProps={{
                      className: 'full-width',
                      error: error && error.new_password,
                      name: 'new-password',
                    }}
                    title='New Password'
                    onChange={(e) => {
                      this.setState({ password: Utils.safeParseEventValue(e) })
                    }}
                    className='input-default full-width mt-4'
                    placeholder='New Password'
                    type='password'
                    name='password1'
                    id='password1'
                  />
                  <InputGroup
                    inputProps={{
                      className: 'full-width',
                      error: error && error.new_password2,
                      name: 'new-password2',
                    }}
                    title='Confirm New Password'
                    onChange={(e) => {
                      this.setState({ password2: Utils.safeParseEventValue(e) })
                    }}
                    className='input-default full-width'
                    placeholder='Confirm New Password'
                    type='password'
                    name='password2'
                    id='password2'
                  />
                  <div className='text-right'>
                    <Button type='submit' disabled={!isValid}>
                      Set password
                    </Button>
                  </div>
                </form>
              )}
              <div>
                {error ? (
                  <div>
                    <h3 className='pt-5'>Oops</h3>
                    <ErrorMessage
                      error='We could not reset your password with the details
                      provided, please try again.'
                    ></ErrorMessage>
                  </div>
                ) : (
                  <div />
                )}
              </div>
            </div>
          )}
        </AccountProvider>
      </div>
    )
  }
}

PasswordResetPage.propTypes = {
  history: RequiredObject,
  location: RequiredObject,
  match: RequiredObject,
}

module.exports = PasswordResetPage
