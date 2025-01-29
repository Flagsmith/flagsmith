import React from 'react'

interface LogoutIconProps {
  className?: string
}

const LogoutIcon: React.FC<LogoutIconProps> = ({ className }) => {
  return (
    <svg className={className} width={18} height={14} viewBox='0 0 18 14'>
      <path
        d='M6.3 13.44H3.36A3.36 3.36 0 010 10.08V3.36A3.36 3.36 0 013.36 0H6.3c.231 0 .42.189.42.42v1.4c0 .231-.189.42-.42.42H3.36c-.62 0-1.12.5-1.12 1.12v6.72c0 .62.5 1.12 1.12 1.12H6.3c.231 0 .42.189.42.42v1.4c0 .231-.189.42-.42.42zm4.126-10.609l2.716 2.489H6.44a.838.838 0 00-.84.84v1.12c0 .465.374.84.84.84h6.702l-2.716 2.488a.843.843 0 00-.028 1.215l.767.766a.843.843 0 001.186.004l5.32-5.278a.839.839 0 000-1.194L12.355.851a.84.84 0 00-1.187.003l-.766.766a.838.838 0 00.024 1.211z'
        fill='#FFF'
        fillRule='nonzero'
      />
    </svg>
  )
}

export default LogoutIcon
