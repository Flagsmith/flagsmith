import { FC, ReactNode } from 'react'
import ContentCard from 'components/base/grid/ContentCard'

type StatCardProps = {
  label: string
  value?: ReactNode
  loading?: boolean
}

const StatCard: FC<StatCardProps> = ({ label, loading, value }) => (
  <ContentCard compact>
    <div className='text-secondary fs-caption'>{label}</div>
    <h4 className='mb-0 mt-1'>
      {loading ? <span className='text-secondary'>—</span> : value ?? '—'}
    </h4>
  </ContentCard>
)

export default StatCard
