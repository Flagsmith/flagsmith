import React, { FC } from 'react'
import { Res } from 'common/types/responses'
import { IconName } from 'components/icons/Icon'
import StatItem from 'components/StatItem'

type TotalItem = {
  colour: string | undefined
  icon: IconName
  limit: number | null | undefined
  title: string
  tooltip?: string
  value: number
}

interface UsageChartTotalsProps {
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

  const totalItems: TotalItem[] = [
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
      limit: undefined,
      title: 'Total API Calls',
      tooltip: maxApiCalls
        ? `Your plan limit is ${maxApiCalls.toLocaleString()} / month`
        : undefined,
      value: data.totals.total,
    },
  ]

  return (
    <Row className='plan p-4 mb-4 flex-wrap gap-4'>
      {totalItems
        .filter((item) => item.value)
        .map((item) => (
          <StatItem
            key={item.title}
            icon={item.icon}
            label={item.title}
            value={item.value}
            limit={item.limit}
            tooltip={item.tooltip}
            visibilityToggle={
              withColor && item.colour
                ? {
                    colour: item.colour,
                    isVisible: selection.includes(item.title),
                    onToggle: () => updateSelection(item.title),
                  }
                : undefined
            }
          />
        ))}
    </Row>
  )
}

export default UsageChartTotals
