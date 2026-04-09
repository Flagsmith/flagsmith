import React, { FC } from 'react'
import Icon from 'components/icons/Icon'
import { Variation } from 'components/experiments-v2/types'
import './VariationTable.scss'

type VariationTableProps = {
  variations: Variation[]
  editable?: boolean
  onRemove?: (id: string) => void
}

const VariationTable: FC<VariationTableProps> = ({
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

      {variations.map((variation) => (
        <div key={variation.id} className='variation-table__row'>
          <div className='variation-table__cell variation-table__cell--name'>
            <span
              className='variation-table__dot'
              style={{ background: variation.colour }}
            />
            <span className='variation-table__name-text'>{variation.name}</span>
            {variation.name === 'Control' && (
              <span className='variation-table__control-tag'>control</span>
            )}
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
