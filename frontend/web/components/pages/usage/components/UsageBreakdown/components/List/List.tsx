import { FC } from 'react'
import EmptyState from 'components/EmptyState'
import { Button } from 'components/base/forms/Button'
import { THROTTLED } from 'components/pages/usage/throttle'
import Row from 'components/pages/usage/components/UsageBreakdown/components/Row'
import {
  BreakdownRow,
  BreakdownStatus,
  sharesOf,
} from 'components/pages/usage/components/UsageBreakdown/utils'

export type ListProps = {
  rows: BreakdownRow[]
  status?: BreakdownStatus
  onRetry?: () => void
}

const List: FC<ListProps> = ({ onRetry, rows, status = 'ready' }) => {
  if (status === 'needs-project') {
    return (
      <EmptyState
        title='Select a project'
        description='Choose a project above to see usage by environment.'
        icon='layers'
      />
    )
  }

  if (status === 'loading') {
    return (
      <div
        className='text-center py-5'
        role='status'
        aria-label='Loading breakdown'
      >
        <Loader />
      </div>
    )
  }

  if (status === 'error' || status === 'throttled') {
    const throttled = status === 'throttled'
    return (
      <div role='alert'>
        <EmptyState
          title={throttled ? THROTTLED.title : 'Breakdown could not be loaded'}
          description={
            throttled
              ? THROTTLED.description
              : 'Something went wrong fetching this breakdown. Try again in a moment.'
          }
          icon='bar-chart'
          action={
            onRetry && (
              <Button theme='secondary' onClick={onRetry}>
                Try again
              </Button>
            )
          }
        />
      </div>
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
