import { FC } from 'react'
import EmptyState from 'components/EmptyState'
import Row from 'components/pages/usage/components/UsageBreakdown/components/Row'
import {
  BreakdownRow,
  sharesOf,
} from 'components/pages/usage/components/UsageBreakdown/utils'

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
  const shares = sharesOf(rows.map((row) => row.value))

  return (
    <div>
      {rows.map((row, index) => (
        <Row
          key={row.key}
          label={row.label}
          value={row.value}
          colour={row.colour}
          largest={largest}
          share={shares[index]}
        />
      ))}
    </div>
  )
}

export default List
