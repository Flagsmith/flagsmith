import React, { FC } from 'react'
import { Link } from 'react-router-dom'
import LabelWithTooltip from 'components/base/LabelWithTooltip'
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
            <LabelWithTooltip label={label} tooltip={tooltip} />
          </Link>
        ) : (
          <p className='metric-label'>
            <LabelWithTooltip label={label} tooltip={tooltip} />
          </p>
        )}
      </div>
      <p className='metric-value'>{value}</p>
    </div>
  )
}

export default EnvironmentMetric
