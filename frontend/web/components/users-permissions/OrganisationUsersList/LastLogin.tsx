import React from 'react'
import moment from 'moment'

interface LastLoginProps {
  lastLogin: string
}

const LastLogin: React.FC<LastLoginProps> = ({ lastLogin }) => {
  const formatLastLogin = (
    last_login: string | undefined,
  ): {
    relativeDate: string
    date?: string
  } => {
    if (!last_login) return { relativeDate: 'Never' }

    const diff = moment().diff(moment(last_login), 'days')

    if (diff === 0) return { relativeDate: 'Today' }
    if (diff === 1) return { relativeDate: 'Yesterday' }
    if (diff >= 30)
      return {
        date: moment(last_login).format('Do MMM YYYY'),
        relativeDate: `${diff} days ago`,
      }

    return { relativeDate: `${diff} days ago` }
  }

  const { date, relativeDate } = formatLastLogin(lastLogin)
  return (
    <div className='fs-small lh-sm'>
      <div className='mb-1'>
        {relativeDate}
        <br />
        {!!date && <div className='list-item-subtitle'>{date}</div>}
      </div>
    </div>
  )
}

export default LastLogin
