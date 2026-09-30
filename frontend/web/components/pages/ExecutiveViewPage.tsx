import React, { FC } from 'react'
import PageTitle from 'components/PageTitle'
import Text from 'components/base/Text'

const ExecutiveViewPage: FC = () => {
  return (
    <div className='app-container container'>
      <PageTitle title='Executive View'>
        High-level insights and analytics across your organisation.
      </PageTitle>

      <div className='text-center py-5'>
        <Text variant='h2' level={2} className='text-muted'>
          Coming Soon
        </Text>
        <p className='text-muted mt-3'>
          This view will provide executive-level insights and analytics.
        </p>
      </div>
    </div>
  )
}

export default ExecutiveViewPage
