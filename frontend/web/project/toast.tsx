import React, { FC, useEffect, useState } from 'react'
import cn from 'classnames'
import { close } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'

import Utils from 'common/utils/utils'
import {
  colorIconDanger,
  colorIconSuccess,
  colorIconWarning,
} from 'common/theme/tokens'
import Icon from 'components/icons/Icon'
import Button from 'components/base/forms/Button'

type ThemeType = 'danger' | 'success' | 'warning'

const themeClassNames: Record<ThemeType, string> = {
  danger: 'alert-danger',
  success: 'alert',
  warning: 'alert-warning',
}

const themeHeadings: Record<ThemeType, string> = {
  danger: 'Error',
  success: 'Success',
  warning: 'Warning',
}

interface MessageProps {
  action?: { buttonText: string; onClick: () => void }
  remove: () => void
  expiry?: number
  isRemoving?: boolean
  theme?: ThemeType
  children?: React.ReactNode
}

type ToastIconType = { theme: ThemeType }

const ToastIcon: FC<ToastIconType> = ({ theme }) => {
  if (theme === 'warning') {
    return <Icon name='warning' width={28} fill={colorIconWarning} />
  }
  return theme === 'danger' ? (
    <Icon name='close-circle' width={28} fill={colorIconDanger} />
  ) : (
    <Icon name='checkmark-circle' width={28} fill={colorIconSuccess} />
  )
}

const Message: FC<MessageProps> = ({
  action,
  children,
  expiry = 5000,
  isRemoving = false,
  remove,
  theme: _theme,
}) => {
  const theme = _theme || 'success'
  useEffect(() => {
    const timeout = setTimeout(remove, expiry)
    return () => clearTimeout(timeout)
  }, [remove, expiry])

  const className = cn(
    'alert toast-message',
    {
      'removing-out': isRemoving,
      'show': !isRemoving,
    },
    themeClassNames[theme],
  )

  const hasAction = action?.onClick && action?.buttonText

  return (
    <div className={className}>
      <div className='my-2 w-100 d-flex flex-nowrap gap-2'>
        <ToastIcon theme={theme} />
        <div className='flex-1 flex-column'>
          <div className='text-default mb-1 fw-semibold'>
            {themeHeadings[theme]}
          </div>
          <div className='text-default fw-normal mb-1'>{children} </div>
          {hasAction && (
            <div className='d-flex'>
              <Button
                className='text-wrap mt-2'
                size='xSmall'
                theme={theme === 'warning' ? 'secondary' : theme}
                onClick={action?.onClick}
              >
                {action?.buttonText}
              </Button>
            </div>
          )}
        </div>
        <a className='toast-message__close' onClick={remove}>
          <span className='icon'>
            <IonIcon icon={close} style={{ fontSize: '16px' }} />
          </span>
        </a>
      </div>
    </div>
  )
}

interface Message {
  action?: { buttonText: string; onClick: () => void }
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
    action?: { buttonText: string; onClick: () => void },
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
        >
          {message.content}
        </Message>
      ))}
    </div>
  )
}

export default ToastMessages
