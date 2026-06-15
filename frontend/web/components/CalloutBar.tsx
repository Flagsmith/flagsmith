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

const DARK_PREFIX_COLOR = '#ffffff'
const DARK_LABEL_COLOR = '#F7D56E'

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
  const chevronFill = isDark ? DARK_PREFIX_COLOR : undefined

  return (
    <div style={{ cursor: onClick ? 'pointer' : undefined }} onClick={onClick}>
      <div className='flex-row'>
        <div className='flex flex-1'>
          <div>
            <pre
              className={`hljs-header${isDark ? ' bg-primary900' : ''}`}
              style={isDark ? { color: DARK_LABEL_COLOR } : undefined}
            >
              <span />
              {icon}{' '}
              <span style={isDark ? { color: DARK_PREFIX_COLOR } : undefined}>
                {prefix}
              </span>{' '}
              <span
                className='hljs-description'
                style={isDark ? { color: DARK_LABEL_COLOR } : undefined}
              >
                {label}
              </span>
              <span className='hljs-icon'>
                <Icon name={chevronName} width={16} fill={chevronFill} />
              </span>
            </pre>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CalloutBar
