import React, { FC } from 'react'

interface EnvironmentMetricProps {
  label: string
  value: string | number
}

const EnvironmentMetric: FC<EnvironmentMetricProps> = ({ label, value }) => {
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
      <p className='metric-label'>{label}</p>
      <p className='metric-value'>{value}</p>
    </div>
  )
}

export default EnvironmentMetric
