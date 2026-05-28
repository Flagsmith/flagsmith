import { FC } from 'react'
import { MultivariateOption } from 'common/types/responses'
import ColorSwatch from 'components/ColorSwatch'
import { colorTextAction, colorTextSuccess } from 'common/theme/tokens'
import './VariationTable.scss'

type VariationTableProps = {
  controlValue: string
  variations: MultivariateOption[]
}

const getVariationValue = (mv: MultivariateOption) => {
  if (mv.type === 'unicode') return mv.string_value
  if (mv.type === 'int') return String(mv.integer_value ?? '')
  if (mv.type === 'bool') return String(mv.boolean_value ?? '')
  return ''
}

const VariationTable: FC<VariationTableProps> = ({
  controlValue,
  variations,
}) => {
  return (
    <div className='variation-table'>
      <div className='variation-table__head'>
        <span className='variation-table__th variation-table__th--name'>
          Name
        </span>
        <span className='variation-table__th variation-table__th--desc'>
          Description
        </span>
        <span className='variation-table__th variation-table__th--value'>
          Value
        </span>
      </div>

      <div className='variation-table__row'>
        <div className='variation-table__cell variation-table__cell--name'>
          <ColorSwatch color={colorTextSuccess} size='md' shape='circle' />
          <span className='variation-table__name-text'>Control</span>
          <span className='variation-table__control-tag'>control</span>
        </div>
        <div className='variation-table__cell variation-table__cell--desc'>
          <span className='variation-table__desc-text'>
            Flag&apos;s base value
          </span>
        </div>
        <div className='variation-table__cell variation-table__cell--value'>
          <span className='variation-table__value-badge'>{controlValue}</span>
        </div>
      </div>

      {variations.map((mv) => (
        <div key={mv.id} className='variation-table__row'>
          <div className='variation-table__cell variation-table__cell--name'>
            <ColorSwatch color={colorTextAction} size='md' shape='circle' />
            <span className='variation-table__name-text'>
              {mv.string_value || `Variation ${mv.id}`}
            </span>
          </div>
          <div className='variation-table__cell variation-table__cell--desc'>
            <span className='variation-table__desc-text' />
          </div>
          <div className='variation-table__cell variation-table__cell--value'>
            <span className='variation-table__value-badge'>
              {getVariationValue(mv)}
            </span>
          </div>
        </div>
      ))}
    </div>
  )
}

export default VariationTable
