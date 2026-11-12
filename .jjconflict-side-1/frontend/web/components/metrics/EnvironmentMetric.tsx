import React, { FC } from 'react'
import { Link } from 'react-router-dom'
import Icon from 'components/icons/Icon'
import Tooltip from 'components/Tooltip'
interface EnvironmentMetricProps {
  label: string
  value: string | number
  link?: string
  tooltip?: string
}

const EnvironmentMetric: FC<EnvironmentMetricProps> = ({
  label,
  link,
  tooltip,
  value,
}) => {
  const labelContent = (
    <>
      {label}
      {tooltip && (
        <Tooltip
          title={<Icon name='info-outlined' width={12} height={12} />}
          place='top'
          titleClassName='cursor-pointer ml-1'
        >
          {tooltip}
        </Tooltip>
      )}
    </>
  )
  return (
    <div
      style={{
        alignItems: 'center',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '3px 8px',
        textAlign: 'center',
      }}
    >
      <div className='d-flex items-center gap-1'>
        {link ? (
          <Link to={link} className='metric-label'>
            {labelContent}
          </Link>
        ) : (
          <p className='metric-label'>{labelContent}</p>
        )}
      </div>
      <p className='metric-value'>{value}</p>
    </div>
  )
}

export default EnvironmentMetric
