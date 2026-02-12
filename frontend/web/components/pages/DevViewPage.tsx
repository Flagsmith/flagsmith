import React, { FC } from 'react'
import PageTitle from 'components/PageTitle'

const DevViewPage: FC = () => {
  return (
    <div className='app-container container'>
      <PageTitle title='Dev View'>
        Developer-focused tools and workflows for your organisation.
      </PageTitle>

      <div className='text-center py-5'>
        <h2 className='text-muted'>Coming Soon</h2>
        <p className='text-muted mt-3'>
          This view will provide developer-focused tools and workflows.
        </p>
      </div>
    </div>
  )
}

export default DevViewPage
