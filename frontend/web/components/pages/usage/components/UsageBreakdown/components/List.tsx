import { FC } from 'react'
import EmptyState from 'components/EmptyState'
import Row from './Row'
import { BreakdownRow } from 'components/pages/usage/components/UsageBreakdown/utils'

export type ListProps = {
  rows: BreakdownRow[]
  isLoading?: boolean
  needsProject?: boolean
}

const List: FC<ListProps> = ({ isLoading, needsProject, rows }) => {
  if (isLoading) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  if (needsProject) {
    return (
      <EmptyState
        title='Pick a project'
        description='Environments belong to a project, so choose one above to break its usage down.'
        icon='bar-chart'
      />
    )
  }

  if (!rows.length) {
    return (
      <EmptyState
        title='No usage recorded'
        description='No usage data available for the selected period and project.'
        icon='bar-chart'
      />
    )
  }

  const largest = Math.max(1, ...rows.map((row) => row.value))
  const total = rows.reduce((sum, row) => sum + row.value, 0)

  return (
    <>
      {rows.map((row) => (
        <Row
          key={row.key}
          label={row.label}
          value={row.value}
          colour={row.colour}
          largest={largest}
          total={total}
        />
      ))}
    </>
  )
}

export default List
