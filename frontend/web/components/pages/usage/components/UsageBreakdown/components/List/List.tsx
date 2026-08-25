import { FC } from 'react'
import EmptyState from 'components/EmptyState'
import Row from 'components/pages/usage/components/UsageBreakdown/components/Row'
import { BreakdownRow } from 'components/pages/usage/components/UsageBreakdown/utils'

export type ListProps = {
  rows: BreakdownRow[]
}

const List: FC<ListProps> = ({ rows }) => {
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
