import React from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'

const MaintenancePage: React.FC = () => {
  return (
    <div className='fullscreen-container maintenance justify-content-center'>
      <div className='col-md-6 mt-5' id='sign-up'>
        <h1>Maintenance</h1>
        We are currently undergoing some scheduled maintenance of the admin
        site, this will not affect your application's feature flags.
        <>
          {' '}
          Check{' '}
          <a target='_blank' href='https://x.com/getflagsmith' rel='noreferrer'>
            @getflagsmith
          </a>{' '}
          for updates.
        </>
        <br />
        <p className='small'>
          Sorry for the inconvenience, we will be back up and running shortly.
        </p>
      </div>
    </div>
  )
}

MaintenancePage.displayName = 'MaintenancePage'

export default ConfigProvider(MaintenancePage)
