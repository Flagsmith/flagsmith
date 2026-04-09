import React, { FC } from 'react'
import { LiftDirection } from 'components/experiments-v2/types'
import './ExperimentStatCard.scss'

type ExperimentStatCardProps = {
  label: string
  value: string | number
  subtitle?: string
  trend?: LiftDirection
}

const ExperimentStatCard: FC<ExperimentStatCardProps> = ({
  label,
  subtitle,
  trend,
  value,
}) => {
  return (
    <div className='experiment-stat-card'>
      <span className='experiment-stat-card__label'>{label}</span>
      <span
        className={`experiment-stat-card__value ${
          trend ? `experiment-stat-card__value--${trend}` : ''
        }`}
      >
        {typeof value === 'number' ? value.toLocaleString() : value}
      </span>
      {subtitle && (
        <span className='experiment-stat-card__subtitle'>{subtitle}</span>
      )}
    </div>
  )
}

ExperimentStatCard.displayName = 'ExperimentStatCard'
export default ExperimentStatCard
