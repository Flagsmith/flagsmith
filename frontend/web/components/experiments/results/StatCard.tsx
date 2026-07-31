import { FC, ReactNode } from 'react'
import ContentCard from 'components/base/grid/ContentCard'
import './results.scss'

type StatCardProps = {
  label: string
  value?: ReactNode
  loading?: boolean
}

const StatCard: FC<StatCardProps> = ({ label, loading, value }) => (
  <ContentCard compact>
    <div className='text-secondary fs-caption'>{label}</div>
    <div className='experiment-results__stat-value mt-1'>
      {loading ? <span className='text-secondary'>—</span> : value ?? '—'}
    </div>
  </ContentCard>
)

export default StatCard
