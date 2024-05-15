import React, { FC } from 'react'
import Icon from './Icon'
import Button from './base/forms/Button'
import Constants from 'common/constants'

type WarningMessageType = {
  warningMessage: string
  enabledButton?: boolean
  warningMessageClass?: string
}

const WarningMessage: FC<WarningMessageType> = (props) => {
  const { enabledButton, warningMessage, warningMessageClass } = props
  const warningMessageClassName = `alert alert-warning ${
    warningMessageClass || 'flex-1 align-items-center'
  }`
  return (
    <div
      className={warningMessageClassName}
      style={{ display: warningMessageClass ? 'initial' : '' }}
    >
      <span className='icon-alert'>
        <Icon name='warning' />
      </span>
      {warningMessage}
      {enabledButton && (
        <Button
          className='btn ml-3'
          onClick={() => {
            document.location.replace(Constants.upgradeURL)
          }}
        >
          Upgrade plan
        </Button>
      )}
    </div>
  )
}

export default WarningMessage
