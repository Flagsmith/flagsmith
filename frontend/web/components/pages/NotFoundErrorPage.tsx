import React, { FC, useEffect } from 'react'
import Constants from 'common/constants'

const NotFoundErrorPage: FC = () => {
  useEffect(() => {
    API.trackPage(Constants.pages.COMING_SOON)
  }, [])

  return (
    <div className='app-container container'>
      <h3 className='pt-5'>Oops!</h3>
      <p>
        It looks like you do not have permission to view this{' '}
        {Utils.fromParam().entity || 'page'}. Please contact a member with
        administrator privileges.
      </p>
    </div>
  )
}

export default NotFoundErrorPage
