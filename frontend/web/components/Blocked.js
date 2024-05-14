import React from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'
import Payment from './modals/Payment'

const Blocked = class extends React.Component {
  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  static displayName = 'HomePage'

  constructor(props, context) {
    super(props, context)
    this.state = {}
  }

  render = () => (
    <div className='fullscreen-container maintenance fullscreen-container__grey justify-content-center dark'>
      {!Utils.isSaas() ? (
        <div className='col-md-6 mt-5' id='sign-up'>
          <h1>Please get in touch</h1>
          Your organisation has been disabled. Please get in touch so we can
          discuss enabling your account.
          {
            <>
              {' '}
              <a
                target='_blank'
                href='mailto:support@flagsmith.com'
                rel='noreferrer'
              >
                support@flagsmith.com
              </a>
              .
            </>
          }
        </div>
      ) : (
        <div className='col-md-8 mt-5' id='sign-up'>
          {
            <>
              <div>
                <Button
                  theme='text'
                  onClick={() => {
                    AppActions.logout()
                    window.location.href = `/login`
                  }}
                >
                  Return to Sign in/Sign up page
                </Button>
              </div>
              <Payment
                isDisableAccountText={
                  'Your organisation has been disabled. Please upgrade your plan or get in touch so we can discuss enabling your account.'
                }
              />
            </>
          }
        </div>
      )}
    </div>
  )
}

module.exports = ConfigProvider(Blocked)
