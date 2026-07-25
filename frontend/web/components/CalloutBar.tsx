import React, { FC, ReactNode } from 'react'
import Icon from './icons/Icon'

export type CalloutBarTheme = 'light' | 'dark'

type CalloutBarProps = {
  theme?: CalloutBarTheme
  icon: ReactNode
  prefix: ReactNode
  label: ReactNode
  expanded?: boolean
  onClick?: () => void
}

const CalloutBar: FC<CalloutBarProps> = ({
  expanded,
  icon,
  label,
  onClick,
  prefix,
  theme = 'light',
}) => {
  const isDark = theme === 'dark'
  const chevronName = expanded ? 'chevron-down' : 'chevron-right'

  return (
    <div className={onClick ? 'cursor-pointer' : undefined} onClick={onClick}>
      <div className='flex-row'>
        <div
          className='flex flex-1'
          style={isMobile ? { overflowX: 'scroll' } : undefined}
        >
          <div>
            <pre className={`hljs-header${isDark ? ' callout-bar--dark' : ''}`}>
              <span />
              {icon} <span>{prefix}</span>{' '}
              <span className='hljs-description'>{label}</span>
              <span className='hljs-icon'>
                <Icon name={chevronName} width={16} />
              </span>
            </pre>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CalloutBar
