import React, { FC } from 'react'
import Text from 'components/base/Text'

type NotFoundPageType = {}

const NotFoundPage: FC<NotFoundPageType> = ({}) => {
  return (
    <div className='app-container container'>
      <Text variant='h3' level={1} className='pt-5'>
        Oops, we can't seem to find this page!
      </Text>
      <p>Please check the URL you are trying to visit and try again.</p>
    </div>
  )
}

export default NotFoundPage
