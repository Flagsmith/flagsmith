import { FC, ReactNode } from 'react'
import './AuditLogList.scss'

type AuditLogDayProps = {
  dayKey: string
  label: string
  children: ReactNode
}

const AuditLogDay: FC<AuditLogDayProps> = ({ children, dayKey, label }) => {
  const headingId = `audit-log-day-${dayKey}`
  return (
    <section aria-labelledby={headingId}>
      <h3
        id={headingId}
        className='audit-log-list__day m-0 fs-captionSmall lh-sm fw-semibold text-secondary bg-surface-subtle px-3 py-2'
      >
        {label}
      </h3>
      {children}
    </section>
  )
}

export default AuditLogDay
