import React, { FC, ReactNode } from 'react'
import Icon from './icons/Icon'

type WarningMessageType = {
  warningMessage: ReactNode
  warningMessageClass?: string
}

const WarningMessage: FC<WarningMessageType> = (props) => {
  const { warningMessage, warningMessageClass } = props
  const warningMessageClassName = `alert alert-warning ${
    warningMessageClass || 'flex-1 align-items-center'
  }`
  if (!props.warningMessage) {
    return null
  }
  return (
    <div
      className={warningMessageClassName}
      style={{ display: warningMessageClass ? 'initial' : '' }}
    >
      <span className='icon-alert'>
        <Icon name='warning' />
      </span>
      {warningMessage}
    </div>
  )
}

export default WarningMessage
