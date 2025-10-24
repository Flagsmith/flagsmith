import React, { FC } from 'react'

const AppLoader: FC = () => {
  return (
    <div
      style={{
        position: 'absolute',
        textAlign: 'center',
        top: '35%',
        width: '100%',
      }}
    >
      <Loader />
    </div>
  )
}

export default AppLoader
