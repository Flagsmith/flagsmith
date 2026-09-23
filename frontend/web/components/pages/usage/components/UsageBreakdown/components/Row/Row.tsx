import { FC } from 'react'
import Format from 'common/utils/format'
import { colorSurfaceAction } from 'common/theme/tokens'
import ColorSwatch from 'components/ColorSwatch'
import ValueBar from 'components/shared/ValueBar'
import { barPercent } from 'components/pages/usage/components/UsageBreakdown/utils'
import './Row.scss'

export type RowProps = {
  label: string
  value: number
  largest: number
  share: number
  colour?: string
}

const Row: FC<RowProps> = ({ colour, label, largest, share, value }) => (
  <div className='usage-breakdown-row d-flex align-items-center gap-3 border-top border-default'>
    <div className='usage-breakdown-row__label d-flex align-items-center gap-2'>
      {colour && <ColorSwatch color={colour} size='sm' />}
      <span className='usage-breakdown-row__name' title={label}>
        {label}
      </span>
    </div>

    <ValueBar
      className='usage-breakdown-row__track'
      percent={barPercent(value, largest)}
      colour={colour ?? colorSurfaceAction}
    />

    <div className='usage-breakdown-row__value text-end fw-bold'>
      {Format.shortenNumber(value)}
    </div>
    <div className='usage-breakdown-row__share text-end fs-captionSmall text-secondary'>
      {share}%
    </div>
  </div>
)

export default Row
