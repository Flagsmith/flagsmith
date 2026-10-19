import React from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'
import Link from './base/link'

const HomePage = class extends React.Component {
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
            <Link target='_blank' href='https://x.com/getflagsmith'>
              @getflagsmith
            </Link>{' '}
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

export default ConfigProvider(HomePage)
