import React, { FC } from 'react'
import { Link } from 'react-router-dom'
import Tooltip from 'components/Tooltip'
import Icon from 'components/Icon'

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
  const LabelWithTooltip = () => {
    return (
      <>
        {label}{' '}
        {tooltip && (
          <Tooltip
            title={<Icon name='info-outlined' width={12} height={12} />}
            place='top'
            titleClassName='cursor-pointer'
          >
            {tooltip}
          </Tooltip>
        )}
      </>
    )
  }

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
            <LabelWithTooltip />
          </Link>
        ) : (
          <p className='metric-label'>
            <LabelWithTooltip />
          </p>
        )}
      </div>
      <p className='metric-value'>{value}</p>
    </div>
  )
}

export default EnvironmentMetric
