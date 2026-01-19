import React, { FC } from 'react'
import Utils from 'common/utils/utils'
import { IonIcon } from '@ionic/react'
import { checkmarkSharp } from 'ionicons/icons'
import { Res } from 'common/types/responses'
import Icon, { IconName } from 'components/Icon'

type LegendItemType = {
  title: string
  value: number
  limit?: number | null
  selection: string[]
  onChange: (v: string) => void
  colour?: string
  icon: IconName
}

const LegendItem: FC<LegendItemType> = ({
  colour,
  icon,
  limit,
  onChange,
  selection,
  title,
  value,
}) => {
  if (!value) {
    return null
  }
  return (
    <div className='d-flex flex-row align-items-start gap-2 mr-4'>
      <div className='plan-icon flex-shrink-0'>
        <Icon name={icon} width={32} fill='#1A2634' />
      </div>
      <div>
        <p className='fs-small lh-sm mb-0'>{title}</p>
        <h4 className='mb-0'>
          {Utils.numberWithCommas(value)}
          {limit !== null && limit !== undefined && (
            <span className='text-muted fs-small fw-normal'>
              {' '}
              / {Utils.numberWithCommas(limit)}
            </span>
          )}
        </h4>
        {!!colour && (
          <div
            className='cursor-pointer d-flex align-items-center gap-2 mt-1'
            onClick={() => onChange(title)}
          >
            <div
              className='d-flex align-items-center justify-content-center text-white'
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
            <span className='text-muted fs-small'>Visible</span>
          </div>
        )}
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
  maxApiCalls?: number | null
}

const UsageChartTotals: FC<UsageChartTotalsProps> = ({
  colours,
  data,
  maxApiCalls,
  selection,
  updateSelection,
  withColor = true,
}) => {
  if (!data?.totals) {
    return null
  }

  const totalItems: Array<{
    colour: string | undefined
    icon: IconName
    limit: number | null | undefined
    title: string
    value: number
  }> = [
    {
      colour: colours[0],
      icon: 'features',
      limit: undefined,
      title: 'Flags',
      value: data.totals.flags,
    },
    {
      colour: colours[1],
      icon: 'person',
      limit: undefined,
      title: 'Identities',
      value: data.totals.identities,
    },
    {
      colour: colours[2],
      icon: 'file-text',
      limit: undefined,
      title: 'Environment Document',
      value: data.totals.environmentDocument,
    },
    {
      colour: colours[3],
      icon: 'layers',
      limit: undefined,
      title: 'Traits',
      value: data.totals.traits,
    },
    {
      colour: undefined,
      icon: 'bar-chart',
      limit: maxApiCalls,
      title: 'Total API Calls',
      value: data.totals.total,
    },
  ]

  return (
    <Row className='plan p-4 mb-4 flex-wrap gap-4'>
      {totalItems.map((item) => (
        <LegendItem
          key={item.title}
          selection={selection}
          onChange={updateSelection}
          colour={!withColor ? undefined : item.colour}
          icon={item.icon}
          limit={item.limit}
          value={item.value}
          title={item.title}
        />
      ))}
    </Row>
  )
}

export default UsageChartTotals
