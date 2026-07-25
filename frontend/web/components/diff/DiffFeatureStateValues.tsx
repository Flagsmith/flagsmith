import React, { FC } from 'react'
import { FlagsmithValue } from 'common/types/responses'
import DiffString from './DiffString'
import DiffEnabled from './DiffEnabled'

type DiffFeatureStateValuesType = {
  enabled: { oldValue: boolean; newValue: boolean }
  value: { oldValue: FlagsmithValue; newValue: FlagsmithValue }
  hideValue?: boolean
}

const enabledWidth = 110

// Renders the shared "Enabled / Value" diff table used when comparing two
// feature states (e.g. a change request version or a segment override).
const DiffFeatureStateValues: FC<DiffFeatureStateValuesType> = ({
  enabled,
  hideValue,
  value,
}) => (
  <div className='panel-content'>
    <div className='search-list mt-2'>
      <div className='flex-row gap-5 table-header'>
        <div
          style={{ width: enabledWidth }}
          className='table-column flex-row text-center'
        >
          Enabled
        </div>
        {!hideValue && (
          <div className='table-column flex-row flex flex-1'>Value</div>
        )}
      </div>
      <div className='flex-row pt-4 gap-5 list-item list-item-sm'>
        <div
          style={{ width: enabledWidth }}
          className='table-column text-center'
        >
          <div className='d-flex flex-row'>
            <DiffEnabled
              oldValue={enabled.oldValue}
              newValue={enabled.newValue}
            />
          </div>
        </div>
        {!hideValue && (
          <div className='table-column flex flex-1 overflow-hidden'>
            <div>
              <DiffString oldValue={value.oldValue} newValue={value.newValue} />
            </div>
          </div>
        )}
      </div>
    </div>
  </div>
)

export default DiffFeatureStateValues
