import React, { FC, useEffect, useState } from 'react'
import cn from 'classnames'
import { close } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'

import Utils from 'common/utils/utils'
import Button from 'components/base/forms/Button'

export type ThemeType = 'danger' | 'info' | 'success' | 'warning'

const themeClassNames: Record<ThemeType, string> = {
  danger: 'alert-danger',
  info: 'alert-info',
  success: 'alert',
  warning: 'alert-warning',
}

export interface MessageProps {
  action?: { buttonText: string; onClick: () => void }
  remove: () => void
  expiry?: number
  isRemoving?: boolean
  theme?: ThemeType
  children?: React.ReactNode
  extraStyles?: { size?: 'large' | undefined }
}

const Message: FC<MessageProps> = ({
  action,
  children,
  expiry = 5000,
  extraStyles,
  isRemoving = false,
  remove,
  theme = 'success',
}) => {
  useEffect(() => {
    const timeout = setTimeout(remove, expiry)
    return () => clearTimeout(timeout)
  }, [remove, expiry])

  const className = cn(
    {
      'alert': true,
      'large': extraStyles?.size === 'large',
      'removing-out': isRemoving,
      'show': !isRemoving,
      'toast-message': true,
    },
    themeClassNames[theme],
  )

  const hasAction = action?.onClick && action?.buttonText

  const closeButton = (
    <a style={{ paddingTop: 2 }} onClick={remove}>
      <span className='icon'>
        <IonIcon icon={close} style={{ fontSize: '13px' }} />
      </span>
    </a>
  )

  return (
    <div className={className}>
      <Row space className='flex-nowrap'>
        <div>{children} </div>
        {!hasAction && closeButton}
        {hasAction && (
          <Row className='flex-nowrap'>
            <Button
              className='text-wrap'
              size='xSmall'
              theme='text'
              onClick={action?.onClick}
            >
              {action?.buttonText}
            </Button>
            {closeButton}
          </Row>
        )}
      </Row>
    </div>
  )
}

export interface Message {
  action?: { buttonText: string; onClick: () => void }
  id: string
  content: React.ReactNode
  expiry?: number
  theme?: ThemeType
  isRemoving?: boolean
  extraStyles?: { size?: 'large' | undefined }
}

const ToastMessages: FC<{}> = () => {
  const [messages, setMessages] = useState<Message[]>([])

  const toast = (
    content: React.ReactNode,
    theme?: ThemeType,
    expiry?: number,
    action?: { buttonText: string; onClick: () => void },
    extraStyles?: { size?: 'large' | undefined },
  ) => {
    setMessages((prevMessages) => {
      // Ignore duplicate messages
      if (prevMessages[0]?.content === content) {
        return prevMessages
      }

      const id = Utils.GUID()
      return [
        {
          action,
          content,
          expiry: E2E ? 1000 : expiry,
          extraStyles,
          id,
          theme,
        },
        ...prevMessages,
      ]
    })
  }

  const remove = (id: string) => {
    setMessages((prevMessages) => {
      const index = prevMessages.findIndex((msg) => msg.id === id)
      if (index === -1) return prevMessages

      const newMessages = [...prevMessages]
      newMessages[index] = { ...newMessages[index], isRemoving: true }

      setTimeout(() => {
        setMessages((prev) => prev.filter((msg) => msg.id !== id))
      }, 500)

      return newMessages
    })
  }

  // Attach toast to window for global access
  React.useEffect(() => {
    ;(window as any).toast = toast
  }, [])

  return (
    <div className='toast-messages'>
      {messages.map((message) => (
        <Message
          action={message.action}
          key={message.id}
          isRemoving={message.isRemoving}
          remove={() => remove(message.id)}
          expiry={message.expiry}
          theme={message.theme}
          extraStyles={message.extraStyles}
        >
          {message.content}
        </Message>
      ))}
    </div>
  )
}

export default ToastMessages
