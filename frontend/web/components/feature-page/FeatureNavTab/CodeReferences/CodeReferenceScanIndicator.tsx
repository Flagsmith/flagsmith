import Icon from 'components/Icon'
import { Moment } from 'moment'
import React from 'react'

interface CodeReferenceScanIndicatorProps {
  scanStatus: 'success' | 'warning'
  lastFeatureFoundAt: Moment | null
}

const CodeReferenceScanIndicator: React.FC<CodeReferenceScanIndicatorProps> = ({
  lastFeatureFoundAt,
  scanStatus,
}) => {
  let tooltipText = ''
  switch (true) {
    case scanStatus === 'success':
      tooltipText = 'Last feature reference seen during last scan'
      break
    case scanStatus === 'warning' && !!lastFeatureFoundAt:
      tooltipText = `Last feature reference seen on ${lastFeatureFoundAt.format(
        'MMM D, YYYY',
      )}`
      break
    case scanStatus === 'warning' && !lastFeatureFoundAt:
      tooltipText = 'No valid feature references found'
      break
    default:
      tooltipText = ''
      break
  }
  return (
    <div className='flex items-center'>
      {
        <Tooltip
          title={
            <Icon
              width={14}
              height={14}
              className='mb-1'
              fill={scanStatus === 'success' ? 'green' : 'orange'}
              name={scanStatus === 'success' ? 'checkmark-circle' : 'warning'}
            />
          }
          titleClassName='mb-1'
        >
          {tooltipText}
        </Tooltip>
      }
    </div>
  )
}

export default CodeReferenceScanIndicator
