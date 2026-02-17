import React, { FC, useEffect, useState } from 'react'
import cn from 'classnames'
import { close } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'

import Utils from 'common/utils/utils'
import Button from 'components/base/forms/Button'

export type ThemeType = 'danger' | 'success'

const themeClassNames: Record<ThemeType, string> = {
  danger: 'alert-danger',
  success: 'alert',
}

export interface MessageProps {
  action?: { buttonText: string; onClick: () => void }
  remove: () => void
  expiry?: number
  isRemoving?: boolean
  theme?: ThemeType
  children?: React.ReactNode
}

type ToastIconType = { theme: ThemeType }

const ToastIcon: FC<ToastIconType> = ({ theme }) => {
  return theme === 'danger' ? (
    <svg
      width='28'
      height='28'
      viewBox='0 0 28 28'
      fill='none'
      xmlns='http://www.w3.org/2000/svg'
    >
      <path
        fillRule='evenodd'
        clipRule='evenodd'
        d='M17.1582 15.5084C17.6144 15.9645 17.6144 16.7019 17.1582 17.158C16.9307 17.3855 16.632 17.4999 16.3334 17.4999C16.0347 17.4999 15.736 17.3855 15.5085 17.158L14 15.6495L12.4915 17.158C12.264 17.3855 11.9654 17.4999 11.6667 17.4999C11.368 17.4999 11.0694 17.3855 10.8419 17.158C10.3857 16.7019 10.3857 15.9645 10.8419 15.5084L12.3504 13.9999L10.8419 12.4914C10.3857 12.0352 10.3857 11.2979 10.8419 10.8417C11.298 10.3855 12.0354 10.3855 12.4915 10.8417L14 12.3502L15.5085 10.8417C15.9647 10.3855 16.702 10.3855 17.1582 10.8417C17.6144 11.2979 17.6144 12.0352 17.1582 12.4914L15.6497 13.9999L17.1582 15.5084ZM14 2.33319C7.56704 2.33319 2.33337 7.56686 2.33337 13.9999C2.33337 20.4329 7.56704 25.6665 14 25.6665C20.433 25.6665 25.6667 20.4329 25.6667 13.9999C25.6667 7.56686 20.433 2.33319 14 2.33319Z'
        fill='#EF4D56'
      />
    </svg>
  ) : (
    <svg
      width='28'
      height='28'
      viewBox='0 0 28 28'
      fill='none'
      xmlns='http://www.w3.org/2000/svg'
    >
      <path
        fillRule='evenodd'
        clipRule='evenodd'
        d='M19.0112 11.2064L13.6819 18.2064C13.4626 18.4946 13.1231 18.6649 12.7614 18.6673H12.7532C12.3951 18.6673 12.0567 18.5016 11.8351 18.2193L8.99774 14.5944C8.60107 14.0881 8.68974 13.3543 9.19724 12.9576C9.70357 12.5598 10.4386 12.6484 10.8352 13.1571L12.7404 15.5908L17.1551 9.79359C17.5447 9.28142 18.2762 9.18109 18.7907 9.57192C19.3029 9.96276 19.4021 10.6943 19.0112 11.2064ZM14.0004 2.33392C7.55691 2.33392 2.33374 7.55709 2.33374 14.0006C2.33374 20.4429 7.55691 25.6673 14.0004 25.6673C20.4439 25.6673 25.6671 20.4429 25.6671 14.0006C25.6671 7.55709 20.4439 2.33392 14.0004 2.33392Z'
        fill='#27AB95'
      />
    </svg>
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
      <div className='my-2 w-100 d-flex flex-nowrap  text-body gap-2'>
        <ToastIcon theme={theme} />
        <div className='flex-1 flex-column'>
          <div className='text-body mb-1 fw-semibold'>
            {theme === 'success' ? 'Success' : 'Error'}
          </div>
          <div className='fw-normal mb-1'>{children} </div>
          {hasAction && (
            <div className='d-flex'>
              <Button
                className='text-wrap mt-2'
                size='xSmall'
                theme={theme}
                onClick={action?.onClick}
              >
                {action?.buttonText}
              </Button>
            </div>
          )}
        </div>
        <a style={{ paddingTop: 2 }} onClick={remove}>
          <span className='icon'>
            <IonIcon icon={close} style={{ fontSize: '16px' }} />
          </span>
        </a>
      </div>
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
