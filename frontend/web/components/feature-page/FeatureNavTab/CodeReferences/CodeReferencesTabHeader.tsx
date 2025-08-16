import moment, { Moment } from 'moment'
import React from 'react'

interface CodeReferencesTabHeaderProps {
  firstScannedAt: Moment
  lastScannedAt: Moment
}

const CodeReferencesTabHeader: React.FC<CodeReferencesTabHeaderProps> = ({
  firstScannedAt,
  lastScannedAt,
}) => {
  if (!firstScannedAt?.isValid || !lastScannedAt?.isValid) {
    return null
  }

  return (
    <div className='flex flex-col gap-1'>
      <p className='text-sm text-gray-500 mb-0'>
        <span className='fw-bold'>First scanned at</span>:{' '}
        {firstScannedAt.format('DD MMM YYYY')}
      </p>
      <p className='text-sm text-gray-500 mb-0'>
        <span className='fw-bold'>Last scanned at</span>:{' '}
        {moment().diff(lastScannedAt, 'days')} days ago
      </p>
    </div>
  )
}

export default CodeReferencesTabHeader
