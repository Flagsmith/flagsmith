import React from 'react'

export default function AppLoader() {
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
