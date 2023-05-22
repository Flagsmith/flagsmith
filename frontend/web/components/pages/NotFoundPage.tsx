import React, { FC } from 'react'

type NotFoundPageType = {}

const NotFoundPage: FC<NotFoundPageType> = ({}) => {
  return (
    <div className='app-container container'>
      <h3 className='pt-5'>Oops, we can't seem to find this page!</h3>
      <p>
        It looks like you have found a URL that does not exist, please check the
        URL you are trying to visit and try again.
      </p>
    </div>
  )
}

export default NotFoundPage
