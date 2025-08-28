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

export interface UsageChartTotalsProps {
  data: Res['organisationUsage'] | undefined
  selection: string[]
  updateSelection: (key: string) => void
  colours: string[]
  withColor?: boolean
}

const UsageChartTotals: FC<UsageChartTotalsProps> = ({
  colours,
  data,
  selection,
  updateSelection,
  withColor = true,
}) => {
  if (!data?.totals) {
    return null
  }

  const totalItems = [
    {
      colour: colours[0],
      title: 'Flags',
      value: data.totals.flags,
    },
    {
      colour: colours[1],
      title: 'Identities',
      value: data.totals.identities,
    },
    {
      colour: colours[2],
      title: 'Environment Document',
      value: data.totals.environmentDocument,
    },
    {
      colour: colours[3],
      title: 'Traits',
      value: data.totals.traits,
    },
    {
      colour: undefined,
      title: 'Total API Calls',
      value: data.totals.total,
    },
  ]

  return (
    <div className='d-flex gap-5 align-items-start'>
      {totalItems.map((item) => (
        <LegendItem
          key={item.title}
          selection={selection}
          onChange={updateSelection}
          colour={!withColor && item.colour ? '#6837fc' : item.colour}
          value={item.value}
          title={item.title}
        />
      ))}
    </div>
  )
}

export default UsageChartTotals
