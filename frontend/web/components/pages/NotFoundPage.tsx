import React, { FC } from 'react'

type NotFoundPageType = {}

const NotFoundPage: FC<NotFoundPageType> = ({}) => {
  return (
    <div className='app-container container'>
      <h3 className='pt-5'>Oops, we can't seem to find this page!</h3>
      <p>Please check the URL you are trying to visit and try again.</p>
    </div>
  )
}

export default NotFoundPage
