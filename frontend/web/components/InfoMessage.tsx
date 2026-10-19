import React, { useEffect, useState } from 'react'
import Icon, { IconName } from './icons/Icon'
import { FC } from 'react'
import Button from './base/forms/Button'
import IconButton from './base/IconButton'

type InfoMessageType = {
  buttonText?: string
  children?: React.ReactNode
  collapseId?: string
  icon?: IconName
  isClosable?: boolean
  title?: string
  url?: string
  close?: () => void
  defaultClosed?: boolean
}

const InfoMessage: FC<InfoMessageType> = ({
  buttonText,
  children,
  close,
  collapseId,
  defaultClosed = false,
  icon,
  isClosable,
  title = 'NOTE',
  url,
}) => {
  // Retrieve initial collapse state from localStorage
  const [isCollapsed, setIsCollapsed] = useState<boolean>(() => {
    if (collapseId) {
      return JSON.parse(
        localStorage.getItem(`infoMessageCollapsed_${collapseId}`) || 'false',
      )
    }
    return defaultClosed
  })

  useEffect(() => {
    if (collapseId) {
      localStorage.setItem(
        `infoMessageCollapsed_${collapseId}`,
        JSON.stringify(isCollapsed),
      )
    }
  }, [isCollapsed, collapseId])

  const handleOpenNewWindow = () => {
    if (url) {
      window.open(url, '_blank')
    }
  }

  // Toggle collapse state
  const handleToggleCollapse = () => {
    setIsCollapsed((prevState) => !prevState)
  }

  return (
    <div className={'alert alert-info flex-1'}>
      <div className={'flex-fill flex-column gap-2'}>
        <div className='d-flex'>
          <div className='flex-fill align-items-center d-flex gap-2'>
            <div className='flex-fill'>
              <div className='d-flex gap-2 align-items-center'>
                <Icon
                  width={22}
                  height={22}
                  fill={'#0AADDF'}
                  name={icon || 'info'}
                />
                <div className='title'>{title}</div>
              </div>
              {!isCollapsed && <div>{children}</div>}
            </div>
            {!isCollapsed && (
              <>
                {url && buttonText && (
                  <Button onClick={handleOpenNewWindow}>{buttonText}</Button>
                )}
              </>
            )}
            {collapseId && (
              <span
                className='ml-auto lh-1 user-select-none'
                onClick={handleToggleCollapse}
                style={{ cursor: 'pointer' }}
              >
                <Icon name={isCollapsed ? 'chevron-right' : 'chevron-down'} />
              </span>
            )}
          </div>
        </div>
      </div>
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

export default InfoMessage
