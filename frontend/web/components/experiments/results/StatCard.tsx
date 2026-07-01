import { FC, ReactNode } from 'react'
import ContentCard from 'components/base/grid/ContentCard'

type StatCardProps = {
  label: string
  value?: ReactNode
  loading?: boolean
}

const StatCard: FC<StatCardProps> = ({ label, loading, value }) => (
  <ContentCard compact>
    <div className='text-muted fs-caption'>{label}</div>
    <div className='fs-3 mt-1'>
      {loading ? <span className='text-muted'>—</span> : value ?? '—'}
    </div>
  </ContentCard>
)

export default StatCard
