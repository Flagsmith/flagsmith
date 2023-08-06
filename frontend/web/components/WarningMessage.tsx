import React, { FC, useState } from 'react'
import Icon from './Icon'

type WarningMessageType = {
  warningMessage: string
}

const WarningMessage: FC<WarningMessageType> = (props) => {
  const { warningMessage } = props
  return (
    <div className='alert alert-warning flex-1 align-items-center'>
      <span className='icon-alert'>
        <Icon name='warning' />
        </span>
      {warningMessage}
    </div>
  )
}

export default WarningMessage
