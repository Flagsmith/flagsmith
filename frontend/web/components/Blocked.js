import React from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'
import Payment from './modals/Payment'
import BlockedOrgInfo from './BlockedOrgInfo'

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
          <span className='h4'>
            Your organisation has been disabled. Please contact Flagsmith
            support at
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
          </span>
          <BlockedOrgInfo />
        </div>
      ) : (
        <div className='col-md-8 mt-5' id='sign-up'>
          {
            <>
              <Payment
                isDisableAccountText={`Your organisation has been disabled. Please upgrade your plan or contact us:`}
              />
            </>
          }
        </div>
      )}
    </div>
  )
}

module.exports = ConfigProvider(Blocked)
