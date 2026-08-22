import { FC } from 'react'
import Format from 'common/utils/format'
import { colorSurfaceAction } from 'common/theme/tokens'
import ValueBar from 'components/shared/ValueBar'
import './Row.scss'

export type RowProps = {
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
const Row: FC<RowProps> = ({ label, largest, total, value }) => (
  <div className='usage-breakdown-row d-flex align-items-center gap-3 border-top border-default'>
    <div className='usage-breakdown-row__label'>{label}</div>

    <ValueBar
      className='usage-breakdown-row__track'
      percent={share(value, largest)}
      colour={colorSurfaceAction}
    />

    <div className='usage-breakdown-row__value text-end fw-bold'>
      {Format.shortenNumber(value)}
    </div>
    <div className='usage-breakdown-row__share text-end fs-captionSmall text-secondary'>
      {share(value, total)}%
    </div>
  </div>
)

export default Row
