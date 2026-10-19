import React from 'react'
import Icon from 'components/icons/Icon'
import Button from 'components/base/forms/Button'
import IconButton from 'components/base/IconButton'

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
        <div className='fw-semibold'>{title}</div>
        {children}
      </div>
      {url && (
        <Button className='btn my-2' onClick={handleOpenNewWindow}>
          {buttonText}
        </Button>
      )}
      {isClosable && (
        <IconButton
          variant='ghost'
          size='small'
          aria-label='Close'
          onClick={close}
          className='ms-2'
        >
          <Icon name='close' width={16} />
        </IconButton>
      )}
    </div>
  )
}

SuccessMessage.displayName = 'SuccessMessage'

export default SuccessMessage
