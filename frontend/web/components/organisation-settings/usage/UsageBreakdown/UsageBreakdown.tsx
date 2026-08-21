import { FC } from 'react'
import EmptyState from 'components/EmptyState'
import UsageBreakdownRow from './UsageBreakdownRow'
import { BREAKDOWN_DIMENSIONS, BreakdownDimension, BreakdownRow } from './utils'
import './UsageBreakdown.scss'

export type UsageBreakdownProps = {
  dimension: BreakdownDimension
  onChangeDimension: (dimension: BreakdownDimension) => void
  rows: BreakdownRow[]
  isLoading?: boolean
  /** Environments belong to a project, so the dimension needs one chosen. */
  needsProject?: boolean
}

type DimensionOption = (typeof BREAKDOWN_DIMENSIONS)[number]

/**
 * Where the usage came from. Deliberately carries no plan limit: a single
 * request type or project has no allowance of its own, so a limit line here
 * would invite a comparison that means nothing.
 */
const UsageBreakdown: FC<UsageBreakdownProps> = ({
  dimension,
  isLoading,
  needsProject,
  onChangeDimension,
  rows,
}) => {
  const largest = Math.max(1, ...rows.map((row) => row.value))
  const total = rows.reduce((sum, row) => sum + row.value, 0)

  const body = () => {
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

    return rows.map((row) => (
      <UsageBreakdownRow
        key={row.label}
        label={row.label}
        value={row.value}
        largest={largest}
        total={total}
      />
    ))
  }

  return (
    <div className='p-4 mt-3 border border-default rounded-lg bg-surface-default'>
      <div className='d-flex align-items-center justify-content-between gap-3 mb-3'>
        <strong>Where the usage came from</strong>
        <div className='usage-breakdown__dimension'>
          <Select
            onChange={(option: DimensionOption) =>
              onChangeDimension(option.value)
            }
            value={BREAKDOWN_DIMENSIONS.find(
              (option) => option.value === dimension,
            )}
            options={BREAKDOWN_DIMENSIONS}
          />
        </div>
      </div>

      {body()}
    </div>
  )
}

export default UsageBreakdown
