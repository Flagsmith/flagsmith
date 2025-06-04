import React from 'react'
import Icon from 'components/Icon'
import { close as closeIcon } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'
import Button from 'components/base/forms/Button'

interface SuccessMessageProps {
  url?: string
  buttonText?: string
  title?: string
  children?: React.ReactNode
  infoMessageClass?: string
  successStyles?: React.CSSProperties
  isClosable?: boolean
  close?: () => void
}

const SuccessMessage: React.FC<SuccessMessageProps> = ({
  buttonText,
  children,
  close,
  infoMessageClass,
  isClosable,
  successStyles,
  title = 'SUCCESS',
  url,
}) => {
  const handleOpenNewWindow = () => {
    if (url) window.open(url, '_blank')
  }

  const infoMessageClassName = `alert alert-success ${
    infoMessageClass || 'flex-1'
  }`

  const titleDescClass = infoMessageClass ? `${infoMessageClass} body mr-2` : ''

  return (
    <div className={infoMessageClassName} style={{ ...successStyles }}>
      <span className={`icon-alert ${infoMessageClass} info-icon`}>
        <Icon fill='#27AB95' name='checkmark-circle' />
      </span>
      <div className={titleDescClass}>
        <div style={{ fontWeight: 'semi-bold' }}>{title}</div>
        {children}
      </div>
      {url && (
        <Button className='btn my-2' onClick={handleOpenNewWindow}>
          {buttonText}
        </Button>
      )}
      {isClosable && (
        <a onClick={close} className='mt-n2 mr-n2 pl-2'>
          <span className={`icon ${infoMessageClass} close-btn`}>
            <IonIcon icon={closeIcon} />
          </span>
        </a>
      )}
    </div>
  )
}

SuccessMessage.displayName = 'SuccessMessage'

export default SuccessMessage
