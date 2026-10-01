import { FC } from 'react'
import FieldLabel from 'components/base/forms/FieldLabel'
import List from './components/List'
import { BREAKDOWN_DIMENSIONS, BreakdownDimension, BreakdownRow } from './utils'
import './UsageBreakdown.scss'

export type UsageBreakdownProps = {
  dimension: BreakdownDimension
  onChangeDimension: (dimension: BreakdownDimension) => void
  rows: BreakdownRow[]
  scope?: string
  isLoading?: boolean
  isError?: boolean
  needsProject?: boolean
  onRetry?: () => void
}

type DimensionOption = (typeof BREAKDOWN_DIMENSIONS)[number]

const UsageBreakdown: FC<UsageBreakdownProps> = ({
  dimension,
  isError,
  isLoading,
  needsProject,
  onChangeDimension,
  onRetry,
  rows,
  scope,
}) => (
  <div className='p-4 mt-3 border border-default rounded-lg bg-surface-default'>
    <div className='d-flex align-items-end justify-content-between gap-3 mb-3'>
      <div>
        <strong>Where the usage came from</strong>
        {scope && <div className='fs-captionSmall text-secondary'>{scope}</div>}
      </div>
      <div className='usage-breakdown__dimension'>
        <FieldLabel htmlFor='usage-breakdown-dimension'>
          Break down by
        </FieldLabel>
        <Select
          inputId='usage-breakdown-dimension'
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

    <List
      rows={rows}
      isLoading={isLoading}
      isError={isError}
      needsProject={needsProject}
      onRetry={onRetry}
    />
  </div>
)

export default UsageBreakdown
