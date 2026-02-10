import { FC, useMemo } from 'react'
import { IntegrationBreakdown } from 'common/types/responses'
import { SortOrder } from 'common/types/requests'
import PanelSearch from 'components/PanelSearch'

interface IntegrationBreakdownTableProps {
  data: IntegrationBreakdown[]
}

type AggregatedIntegrationRow = {
  integration_type: string
  total_count: number
  org_count: number
}

const IntegrationBreakdownTable: FC<IntegrationBreakdownTableProps> = ({
  data,
}) => {
  const rows = useMemo(() => {
    const grouped: Record<string, AggregatedIntegrationRow> = {}

    data.forEach((item) => {
      if (!grouped[item.integration_type]) {
        grouped[item.integration_type] = {
          integration_type: item.integration_type,
          org_count: 0,
          total_count: 0,
        }
      }
      grouped[item.integration_type].total_count += item.count
      grouped[item.integration_type].org_count += 1
    })

    return Object.values(grouped)
  }, [data])

  return (
    <PanelSearch
      className='no-pad'
      filterRow={(item: AggregatedIntegrationRow, search: string) =>
        item.integration_type.toLowerCase().includes(search.toLowerCase())
      }
      header={
        <div className='table-header d-flex flex-row align-items-center'>
          <div className='table-column flex-fill' style={{ paddingLeft: 20 }}>
            Integration Type
          </div>
          <div className='table-column' style={{ width: 140 }}>
            Total Instances
          </div>
          <div className='table-column' style={{ width: 140 }}>
            Organisations
          </div>
        </div>
      }
      id='integration-breakdown-table'
      items={rows}
      renderRow={(row: AggregatedIntegrationRow) => (
        <div
          className='flex-row list-item'
          style={{ paddingBottom: 12, paddingTop: 12 }}
        >
          <div
            className='flex-fill font-weight-medium'
            style={{ paddingLeft: 20 }}
          >
            {row.integration_type}
          </div>
          <div
            className='table-column font-weight-medium'
            style={{ width: 140 }}
          >
            {row.total_count}
          </div>
          <div
            className='table-column font-weight-medium'
            style={{ width: 140 }}
          >
            {row.org_count}
          </div>
        </div>
      )}
      sorting={[
        {
          default: true,
          label: 'Total Instances',
          order: SortOrder.DESC,
          value: 'total_count',
        },
        {
          label: 'Type',
          order: SortOrder.ASC,
          value: 'integration_type',
        },
        {
          label: 'Organisations',
          order: SortOrder.DESC,
          value: 'org_count',
        },
      ]}
      title='Integrations by Type'
    />
  )
}

export default IntegrationBreakdownTable
