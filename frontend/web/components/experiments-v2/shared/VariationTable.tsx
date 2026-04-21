import React, { FC } from 'react'
import Icon from 'components/icons/Icon'
import { CONTROL_COLOUR, Variation } from 'components/experiments-v2/types'
import './VariationTable.scss'

type VariationTableProps = {
  variations: Variation[]
  /**
   * Renders an implicit "Control" row above the variations, reflecting that
   * control is the flag's base value rather than a peer variation.
   */
  controlValue?: string
  editable?: boolean
  onRemove?: (id: string) => void
}

const VariationTable: FC<VariationTableProps> = ({
  controlValue,
  editable = false,
  onRemove,
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
        {editable && (
          <span className='variation-table__th variation-table__th--actions' />
        )}
      </div>

      {controlValue !== undefined && (
        <div className='variation-table__row'>
          <div className='variation-table__cell variation-table__cell--name'>
            <span
              className='variation-table__dot'
              style={{ background: CONTROL_COLOUR }}
            />
            <span className='variation-table__name-text'>Control</span>
            <span className='variation-table__control-tag'>control</span>
          </div>
          <div className='variation-table__cell variation-table__cell--desc'>
            <span className='variation-table__desc-text'>
              Flag&apos;s base value — the baseline for comparison
            </span>
          </div>
          <div className='variation-table__cell variation-table__cell--value'>
            <span className='variation-table__value-badge'>{controlValue}</span>
          </div>
          {editable && (
            <div className='variation-table__cell variation-table__cell--actions' />
          )}
        </div>
      )}

      {variations.map((variation) => (
        <div key={variation.id} className='variation-table__row'>
          <div className='variation-table__cell variation-table__cell--name'>
            <span
              className='variation-table__dot'
              style={{ background: variation.colour }}
            />
            <span className='variation-table__name-text'>{variation.name}</span>
          </div>
          <div className='variation-table__cell variation-table__cell--desc'>
            <span className='variation-table__desc-text'>
              {variation.description}
            </span>
          </div>
          <div className='variation-table__cell variation-table__cell--value'>
            <span className='variation-table__value-badge'>
              {variation.value}
            </span>
          </div>
          {editable && (
            <div className='variation-table__cell variation-table__cell--actions'>
              <button
                className='variation-table__action-btn'
                onClick={() => onRemove?.(variation.id)}
                type='button'
                aria-label={`Remove ${variation.name}`}
              >
                <Icon name='trash-2' width={18} />
              </button>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

VariationTable.displayName = 'VariationTable'
export default VariationTable
