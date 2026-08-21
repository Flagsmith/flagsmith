import { FC } from 'react'
import Format from 'common/utils/format'
import { colorSurfaceAction } from 'common/theme/tokens'
import './UsageBreakdownRow.scss'

export type UsageBreakdownRowProps = {
  label: string
  value: number
  /** The largest row, so the bars can be compared against each other. */
  largest: number
  /** Everything in the breakdown, so the row can state its share. */
  total: number
}

const share = (value: number, total: number) =>
  total ? Math.round((value / total) * 100) : 0

/**
 * The bar is sized against the largest row and the percentage against the
 * total. One answers "which is biggest", the other "how much of my usage is
 * this", and a single bar cannot say both.
 */
const UsageBreakdownRow: FC<UsageBreakdownRowProps> = ({
  label,
  largest,
  total,
  value,
}) => (
  <div className='usage-breakdown-row'>
    <div className='usage-breakdown-row__label'>{label}</div>

    <div className='usage-breakdown-row__track rounded-full overflow-hidden bg-surface-muted'>
      <div
        className='usage-breakdown-row__fill h-100 rounded-full'
        style={{
          background: colorSurfaceAction,
          width: `${share(value, largest)}%`,
        }}
      />
    </div>

    <div className='usage-breakdown-row__value fw-bold'>
      {Format.shortenNumber(value)}
    </div>
    <div className='usage-breakdown-row__share fs-captionSmall text-secondary'>
      {share(value, total)}%
    </div>
  </div>
)

export default UsageBreakdownRow
