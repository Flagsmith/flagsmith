import React, { FC } from 'react'

interface AppLoaderProps {
  style?: React.CSSProperties
}

const AppLoader: FC<AppLoaderProps> = ({ style }) => {
  return (
    <div
      style={
        style
          ? style
          : {
              position: 'absolute',
              textAlign: 'center',
              top: '35%',
              width: '100%',
            }
      }
    >
      <Loader />
    </div>
  )
}

export default AppLoader
