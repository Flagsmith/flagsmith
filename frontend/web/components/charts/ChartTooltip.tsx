import React, { FC } from 'react'
import { TooltipProps } from 'recharts'
import {
  NameType,
  Payload,
  ValueType,
} from 'recharts/types/component/DefaultTooltipContent'
import ColorSwatch from 'components/ColorSwatch'

type SeriesPayload = Payload<ValueType, NameType>

const formatNumber = (n: ValueType | undefined): string =>
  typeof n === 'number' ? n.toLocaleString() : ''

const numericValue = (v: ValueType | undefined): number =>
  typeof v === 'number' ? v : 0

type ChartTooltipProps = TooltipProps<ValueType, NameType> & {
  /**
   * Optional dataKey → display name map. When a dataKey is a numeric id
   * (e.g. env id) the tooltip would otherwise show that id verbatim — pass
   * a seriesLabels map to render human-readable names instead.
   */
  seriesLabels?: Record<string, string>
}

const ChartTooltip: FC<ChartTooltipProps> = ({
  active,
  label,
  payload,
  seriesLabels,
}) => {
  if (!active || !payload || payload.length === 0) return null
  const total = payload.reduce<number>(
    (sum, el) => sum + numericValue(el.value),
    0,
  )

  return (
    <div className='bg-surface-default border-default rounded-md shadow-md py-2'>
      <div className='px-3 py-1 fs-small fw-semibold text-default'>{label}</div>
      <hr className='border-default my-0 mb-2' />
      {payload.map((el: SeriesPayload) => {
        const key = String(el.dataKey)
        const displayName = seriesLabels?.[key] ?? key
        return (
          <div
            key={key}
            className='d-flex align-items-center gap-2 px-3 py-1 fs-small'
          >
            <ColorSwatch color={el.color ?? ''} size='sm' />
            <span className='text-default'>{displayName}:</span>
            <span className='fw-semibold text-default'>
              {formatNumber(el.value)}
            </span>
          </div>
        )
      })}
      <div className='border-top border-default mt-2 pt-2 px-3 fs-small fw-semibold'>
        Total: {formatNumber(total)}
      </div>
    </div>
  )
}

export default ChartTooltip
