import React, { FC } from 'react'
import Utils from 'common/utils/utils'
import { IonIcon } from '@ionic/react'
import { checkmarkSharp } from 'ionicons/icons'
import { Res } from 'common/types/responses'

type LegendItemType = {
  title: string
  value: number
  selection: string[]
  onChange: (v: string) => void
  colour?: string
}

const LegendItem: FC<LegendItemType> = ({
  colour,
  onChange,
  selection,
  title,
  value,
}) => {
  if (!value) {
    return null
  }
  return (
    <div className='mb-4'>
      <h3 className='mb-2'>{Utils.numberWithCommas(value)}</h3>
      <div
        className='cursor-pointer d-flex align-items-center gap-2'
        onClick={() => onChange(title)}
      >
        {!!colour && (
          <div
            className='text-white d-flex align-items-center justify-content-center'
            style={{
              backgroundColor: colour,
              borderRadius: 2,
              flexShrink: 0,
              height: 16,
              width: 16,
            }}
          >
            {selection.includes(title) && (
              <IonIcon size={'8px'} color='white' icon={checkmarkSharp} />
            )}
          </div>
        )}
        <span className='text-muted'>{title}</span>
      </div>
    </div>
  )
}

export interface UsageTotalsProps {
  data: Res['organisationUsage'] | undefined
  selection: string[]
  updateSelection: (key: string) => void
  colours: string[]
}

const UsageTotals: FC<UsageTotalsProps> = ({
  colours,
  data,
  selection,
  updateSelection,
}) => {
  if (!data?.totals) {
    return null
  }

  return (
    <div className='d-flex gap-5 align-items-start'>
      <LegendItem
        selection={selection}
        onChange={updateSelection}
        colour={colours[0]}
        value={data.totals.flags}
        title='Flags'
      />
      <LegendItem
        selection={selection}
        onChange={updateSelection}
        colour={colours[1]}
        value={data.totals.identities}
        title='Identities'
      />
      <LegendItem
        selection={selection}
        onChange={updateSelection}
        colour={colours[2]}
        value={data.totals.environmentDocument}
        title='Environment Document'
      />
      <LegendItem
        selection={selection}
        onChange={updateSelection}
        colour={colours[3]}
        value={data.totals.traits}
        title='Traits'
      />
      <LegendItem
        selection={selection}
        onChange={updateSelection}
        value={data.totals.total}
        title='Total API Calls'
      />
    </div>
  )
}

export default UsageTotals
