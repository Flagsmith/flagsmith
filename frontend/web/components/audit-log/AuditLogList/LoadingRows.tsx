import { FC } from 'react'
import Skeleton from 'components/Skeleton'
import './AuditLogList.scss'

const LoadingRows: FC = () => (
  <div role='status' aria-label='Loading audit log'>
    {[0, 1, 2].map((i) => (
      <div
        key={i}
        className='audit-log-list__skeleton d-flex align-items-center gap-3 px-3 py-3'
      >
        <Skeleton variant='circle' width={32} height={32} />
        <div className='d-flex flex-column gap-2 flex-fill'>
          <Skeleton width={260 - i * 40} />
          <Skeleton width={140} />
        </div>
        <Skeleton variant='badge' width={80} />
      </div>
    ))}
  </div>
)

export default LoadingRows
