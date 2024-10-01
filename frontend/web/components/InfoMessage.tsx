import React, { PureComponent, useEffect, useState } from 'react'
import Icon, { IconName } from './Icon'
import { chevronForward, close as closeIcon, chevronDown } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'
import { FC } from 'react'

type InfoMessageType = {
  buttonText?: string
  children?: React.ReactNode
  collapseId?: string
  icon?: IconName
  isClosable?: boolean
  title?: string
  url?: string
  close?: () => void
}

const InfoMessage: FC<InfoMessageType> = ({
  buttonText,
  children,
  close,
  collapseId,
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
    return false
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
          <div
            className='user-select-none flex-fill align-items-center d-flex gap-2'
            onClick={handleToggleCollapse}
            style={{ cursor: 'pointer' }}
          >
            <Icon
              width={22}
              height={22}
              fill={'#0AADDF'}
              name={icon || 'info'}
            />
            <div className='title'>{title}</div>
            {collapseId && (
              <span className='ml-auto lh-1'>
                <IonIcon icon={isCollapsed ? chevronForward : chevronDown} />
              </span>
            )}
          </div>
        </div>
        {!isCollapsed && (
          <>
            <div className='flex-fill mt-1'>{children}</div>
            {url && buttonText && (
              <button className='btn my-2 ml-2' onClick={handleOpenNewWindow}>
                {buttonText}
              </button>
            )}
          </>
        )}
      </div>
      {isClosable && (
        <a onClick={close} className='mt-n2 mr-n2 pl-2'>
          <span className={`icon close-btn`}>
            <IonIcon icon={closeIcon} />
          </span>
        </a>
      )}
    </div>
  )
}

export default InfoMessage
