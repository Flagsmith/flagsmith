import React, { FC } from 'react'
import { TooltipProps } from 'recharts'
import {
  NameType,
  ValueType,
} from 'recharts/types/component/DefaultTooltipContent'
import Utils from 'common/utils/utils'

type ChartTooltipProps = TooltipProps<ValueType, NameType> & {
  formatLabel?: (label: string) => string
}

const ChartTooltip: FC<ChartTooltipProps> = ({
  active,
  formatLabel,
  label,
  payload,
}) => {
  if (!active || !payload || payload.length === 0) {
    return null
  }

  const displayLabel = formatLabel ? formatLabel(String(label)) : String(label)

  return (
    <div className='recharts-tooltip py-2'>
      <div className='px-4 py-2 fs-small lh-sm fw-bold recharts-tooltip-header'>
        {displayLabel}
      </div>
      <hr className='py-0 my-0 mb-3' />
      {payload.map((entry) => (
        <Row key={String(entry.dataKey)} className='px-4 mb-3'>
          <span
            className='recharts-tooltip-swatch'
            style={{ backgroundColor: entry.color }}
          />
          <span className='text-muted ml-2'>
            {entry.name || entry.dataKey}:{' '}
            {Utils.numberWithCommas(Number(entry.value))}
          </span>
        </Row>
      ))}
    </div>
  )
}

export default ChartTooltip
