import { FC, useMemo } from 'react'
import { IntegrationBreakdown } from 'common/types/responses'
import { SortOrder } from 'common/types/requests'
import PanelSearch from 'components/PanelSearch'
import Utils from 'common/utils/utils'

interface IntegrationAdoptionTableProps {
  data: IntegrationBreakdown[]
  totalOrganisations: number
}

const integrationMeta: Record<string, { category: string }> = {
  'amplitude': { category: 'Analytics' },
  'datadog': { category: 'Monitoring' },
  'dynatrace': { category: 'Monitoring' },
  'github': { category: 'CI/CD' },
  'grafana': { category: 'Monitoring' },
  'heap': { category: 'Analytics' },
  'jira': { category: 'Project Management' },
  'mixpanel': { category: 'Analytics' },
  'new-relic': { category: 'Monitoring' },
  'rudderstack': { category: 'Analytics' },
  'segment': { category: 'Analytics' },
  'sentry': { category: 'Monitoring' },
  'slack': { category: 'Messaging' },
  'webhook': { category: 'Webhooks' },
}

type AdoptionRow = {
  category: string
  integration_key: string
  org_count: number
  title: string
}

const IntegrationAdoptionTable: FC<IntegrationAdoptionTableProps> = ({
  data,
  totalOrganisations,
}) => {
  const rows = useMemo(() => {
    const integrationData = Utils.getIntegrationData() as Record<
      string,
      { title?: string }
    >

    // Group by integration_type → count unique orgs
    const byKey: Record<string, Set<number>> = {}

    data.forEach((item) => {
      if (!byKey[item.integration_type]) {
        byKey[item.integration_type] = new Set()
      }
      byKey[item.integration_type].add(item.organisation_id)
    })

    return Object.keys(integrationMeta).map((key): AdoptionRow => {
      const meta = integrationMeta[key]
      const config = integrationData[key]

      return {
        category: meta.category,
        integration_key: key,
        org_count: byKey[key]?.size ?? 0,
        title: config?.title || key,
      }
    })
  }, [data])

  return (
    <PanelSearch
      className='no-pad'
      filterRow={(item: AdoptionRow, search: string) => {
        const q = search.toLowerCase()
        return (
          item.title.toLowerCase().includes(q) ||
          item.category.toLowerCase().includes(q)
        )
      }}
      header={
        <div className='table-header d-flex flex-row align-items-center'>
          <div className='table-column flex-fill' style={{ paddingLeft: 20 }}>
            Integration
          </div>
          <div className='table-column' style={{ width: 160 }}>
            Category
          </div>
          <div className='table-column' style={{ width: 160 }}>
            Organisations
          </div>
        </div>
      }
      id='integration-adoption-table'
      items={rows}
      renderRow={(row: AdoptionRow) => (
        <div
          className='flex-row list-item'
          style={{ paddingBottom: 12, paddingTop: 12 }}
        >
          <div
            className='flex-fill d-flex align-items-center font-weight-medium'
            style={{ paddingLeft: 20 }}
          >
            {row.title}
          </div>
          <div
            className='table-column text-muted'
            style={{ fontSize: 13, width: 160 }}
          >
            {row.category}
          </div>
          <div
            className='table-column font-weight-medium'
            style={{ fontSize: 13, width: 160 }}
          >
            {row.org_count} of {totalOrganisations}
          </div>
        </div>
      )}
      sorting={[
        {
          default: true,
          label: 'Adoption',
          order: SortOrder.DESC,
          value: 'org_count',
        },
        {
          label: 'Name',
          order: SortOrder.ASC,
          value: 'title',
        },
        {
          label: 'Category',
          order: SortOrder.ASC,
          value: 'category',
        },
      ]}
      title='Integration Adoption'
    />
  )
}

export default IntegrationAdoptionTable
