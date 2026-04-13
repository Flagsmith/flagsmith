import React, { FC } from 'react'
import { TooltipProps } from 'recharts'
import {
  NameType,
  Payload,
  ValueType,
} from 'recharts/types/component/DefaultTooltipContent'
import ColorSwatch from 'components/ColorSwatch'

type SeriesPayload = Payload<ValueType, NameType>

const formatNumber = (n: number | string | undefined): string =>
  typeof n === 'number' ? n.toLocaleString() : ''

const numericValue = (v: ValueType | undefined): number =>
  typeof v === 'number' ? v : 0

const ChartTooltip: FC<TooltipProps<ValueType, NameType>> = ({
  active,
  label,
  payload,
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
      {payload.map((el: SeriesPayload) => (
        <div
          key={String(el.dataKey)}
          className='d-flex align-items-center gap-2 px-3 py-1 fs-small'
        >
          <ColorSwatch color={el.color ?? ''} size='sm' />
          <span className='text-secondary'>{String(el.dataKey)}:</span>
          <span className='fw-medium'>{formatNumber(el.value)}</span>
        </div>
      ))}
      <div className='border-top border-default mt-2 pt-2 px-3 fs-small fw-semibold'>
        Total: {formatNumber(total)}
      </div>
    </div>
  )
}

export default ChartTooltip
