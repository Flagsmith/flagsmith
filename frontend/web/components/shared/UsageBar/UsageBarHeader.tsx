import { FC } from 'react'

export type UsageBarHeaderProps = {
  label: string
  usage: number
  limit: number
}

/** The label and raw figure above the track. Only shown when a label is given. */
const UsageBarHeader: FC<UsageBarHeaderProps> = ({ label, limit, usage }) => (
  <div className='d-flex justify-content-between align-items-center mb-1'>
    <span className='fs-small fw-normal'>{label}</span>
    <span className='fs-small fw-bold'>
      {usage}/{limit}
    </span>
  </div>
)

export default UsageBarHeader
