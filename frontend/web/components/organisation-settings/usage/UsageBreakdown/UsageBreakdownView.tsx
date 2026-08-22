import { FC } from 'react'
import List from './components/List'
import { BREAKDOWN_DIMENSIONS, BreakdownDimension, BreakdownRow } from './utils'
import './UsageBreakdown.scss'

export type UsageBreakdownViewProps = {
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
 *
 * Totals only, no series over time. The chart above answers "where am I
 * heading against my plan", and a second time chart here would compete with it.
 */
const UsageBreakdownView: FC<UsageBreakdownViewProps> = ({
  dimension,
  isLoading,
  needsProject,
  onChangeDimension,
  rows,
}) => (
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

    <List rows={rows} isLoading={isLoading} needsProject={needsProject} />
  </div>
)

export default UsageBreakdownView
