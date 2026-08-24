import { FC } from 'react'
import Format from 'common/utils/format'
import { colorSurfaceAction } from 'common/theme/tokens'
import ColorSwatch from 'components/ColorSwatch'
import ValueBar from 'components/shared/ValueBar'
import './Row.scss'

export type RowProps = {
  label: string
  value: number
  largest: number
  total: number
  colour?: string
}

const share = (value: number, total: number) =>
  total ? Math.round((value / total) * 100) : 0

const Row: FC<RowProps> = ({ colour, label, largest, total, value }) => (
  <div className='usage-breakdown-row d-flex align-items-center gap-3 border-top border-default'>
    <div className='usage-breakdown-row__label d-flex align-items-center gap-2'>
      {colour && <ColorSwatch color={colour} size='sm' />}
      {label}
    </div>

    <ValueBar
      className='usage-breakdown-row__track'
      percent={share(value, largest)}
      colour={colour ?? colorSurfaceAction}
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
