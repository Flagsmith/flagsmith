import React from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'

const HomePage = class extends React.Component {
  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  static displayName = 'HomePage'

  constructor(props, context) {
    super(props, context)
    this.state = {}
  }

  render = () => (
    <div className='fullscreen-container maintenance justify-content-center'>
      <div className='col-md-6 mt-5' id='sign-up'>
        <h1>Maintenance</h1>
        We are currently undergoing some scheduled maintenance of the admin
        site, this will not affect your application's feature flags.
        {
          <>
            {' '}
            Check{' '}
            <a
              target='_blank'
              href='https://x.com/getflagsmith'
              rel='noreferrer'
            >
              @getflagsmith
            </a>{' '}
            for updates.
          </>
        }
        <br />
        <p className='small'>
          Sorry for the inconvenience, we will be back up and running shortly.
        </p>
      </div>
    </div>
  )
}

module.exports = ConfigProvider(HomePage)
