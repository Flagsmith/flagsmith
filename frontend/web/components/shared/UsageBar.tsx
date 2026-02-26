import { FC } from 'react'

export type UsageBarProps = {
  label: string
  limit: number
  usage: number
}

const UsageBar: FC<UsageBarProps> = ({ label, limit, usage }) => {
  const percentage = limit > 0 ? (usage / limit) * 100 : 0
  const barWidth = Math.min(percentage, 100)

  let colourClass = 'bg-primary'
  if (percentage >= 100) {
    colourClass = 'bg-danger'
  } else if (percentage >= 85) {
    colourClass = 'bg-warning'
  }

  return (
    <div className='mb-2'>
      <div className='d-flex justify-content-between align-items-center mb-1'>
        <span className='fs-small fw-normal'>{label}</span>
        <span className='fs-small fw-bold'>
          {usage}/{limit}
        </span>
      </div>
      <div className='progress' style={{ height: '8px' }}>
        <div
          className={`progress-bar ${colourClass}`}
          role='progressbar'
          style={{ width: `${barWidth}%` }}
        />
      </div>
    </div>
  )
}

export default UsageBar
