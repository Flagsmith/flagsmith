import React, { FC } from 'react'
import PageTitle from 'components/PageTitle'

const ExecutiveViewPage: FC = () => {
  return (
    <div className='app-container container'>
      <PageTitle title='Executive View'>
        High-level insights and analytics across your organisation.
      </PageTitle>

      <div className='text-center py-5'>
        <h2 className='text-muted'>Coming Soon</h2>
        <p className='text-muted mt-3'>
          This view will provide executive-level insights and analytics.
        </p>
      </div>
    </div>
  )
}

export default ExecutiveViewPage
