import React, { FC, useEffect, useState } from 'react'
import cn from 'classnames'
import { close } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'

import Utils from 'common/utils/utils'

export type ThemeType = 'danger' | 'info' | 'success' | 'warning'

const themeClassNames: Record<ThemeType, string> = {
  danger: 'alert-danger',
  info: 'alert-info',
  success: 'alert',
  warning: 'alert-warning',
}

export interface MessageProps {
  remove: () => void
  expiry?: number
  isRemoving?: boolean
  theme?: ThemeType
  children?: React.ReactNode
}

const Message: FC<MessageProps> = ({
  children,
  expiry = 5000,
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
      'removing-out': isRemoving,
      'show': !isRemoving,
      'toast-message': true,
    },
    themeClassNames[theme],
  )

  return (
    <div className={className}>
      <Row space className='flex-nowrap'>
        <span>{children} </span>
        <a style={{ paddingTop: 2 }} onClick={remove}>
          <span className='icon'>
            <IonIcon icon={close} style={{ fontSize: '13px' }} />
          </span>
        </a>
      </Row>
    </div>
  )
}

export interface Message {
  id: string
  content: React.ReactNode
  expiry?: number
  theme?: ThemeType
  isRemoving?: boolean
}

const ToastMessages: FC<{}> = () => {
  const [messages, setMessages] = useState<Message[]>([])

  const toast = (
    content: React.ReactNode,
    theme?: ThemeType,
    expiry?: number,
  ) => {
    setMessages((prevMessages) => {
      // Ignore duplicate messages
      if (prevMessages[0]?.content === content) {
        return prevMessages
      }

      const id = Utils.GUID()
      return [
        {
          content,
          expiry: E2E ? 1000 : expiry,
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
          key={message.id}
          isRemoving={message.isRemoving}
          remove={() => remove(message.id)}
          expiry={message.expiry}
          theme={message.theme}
        >
          {message.content}
        </Message>
      ))}
    </div>
  )
}

export default ToastMessages
