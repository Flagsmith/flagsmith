import { FC, useMemo } from 'react'
import { ReleasePipelineStats } from 'common/types/responses'
import { SortOrder } from 'common/types/requests'
import PanelSearch from 'components/PanelSearch'

interface ReleasePipelineStatsTableProps {
  stats: ReleasePipelineStats[]
}

type AggregatedPipelineRow = {
  organisation_name: string
  project_name: string
  stages: Record<string, number>
  total_flags: number
}

const ReleasePipelineStatsTable: FC<ReleasePipelineStatsTableProps> = ({
  stats,
}) => {
  const { rows, stages } = useMemo(() => {
    const stageSet = new Set<string>()
    const grouped: Record<string, AggregatedPipelineRow> = {}

    stats.forEach((s) => {
      stageSet.add(s.stage)
      const key = `${s.organisation_id}-${s.project_id}`
      if (!grouped[key]) {
        grouped[key] = {
          organisation_name: s.organisation_name,
          project_name: s.project_name,
          stages: {},
          total_flags: 0,
        }
      }
      grouped[key].stages[s.stage] = s.flag_count
      grouped[key].total_flags += s.flag_count
    })

    return {
      rows: Object.values(grouped),
      stages: Array.from(stageSet),
    }
  }, [stats])

  return (
    <PanelSearch
      className='no-pad'
      filterRow={(item: AggregatedPipelineRow, search: string) =>
        item.organisation_name.toLowerCase().includes(search.toLowerCase()) ||
        item.project_name.toLowerCase().includes(search.toLowerCase())
      }
      header={
        <div className='table-header d-flex flex-row align-items-center'>
          <div className='table-column flex-fill' style={{ paddingLeft: 20 }}>
            Organisation / Project
          </div>
          {stages.map((stage) => (
            <div key={stage} className='table-column' style={{ width: 120 }}>
              {stage}
            </div>
          ))}
          <div className='table-column' style={{ width: 100 }}>
            Total
          </div>
        </div>
      }
      id='release-pipeline-stats-table'
      items={rows}
      paging={rows.length > 10 ? { goToPage: 1, pageSize: 10 } : undefined}
      renderRow={(row: AggregatedPipelineRow) => (
        <div
          className='flex-row list-item'
          style={{ paddingBottom: 12, paddingTop: 12 }}
        >
          <div className='flex-fill' style={{ paddingLeft: 20 }}>
            <div className='font-weight-medium'>{row.project_name}</div>
            <div className='text-muted' style={{ fontSize: 12 }}>
              {row.organisation_name}
            </div>
          </div>
          {stages.map((stage) => (
            <div
              key={stage}
              className='table-column font-weight-medium'
              style={{ width: 120 }}
            >
              {row.stages[stage] || 0}
            </div>
          ))}
          <div
            className='table-column font-weight-medium'
            style={{ width: 100 }}
          >
            {row.total_flags}
          </div>
        </div>
      )}
      sorting={[
        {
          default: true,
          label: 'Project',
          order: SortOrder.ASC,
          value: 'project_name',
        },
        {
          label: 'Total Flags',
          order: SortOrder.DESC,
          value: 'total_flags',
        },
      ]}
      title='Release Pipeline Statistics'
    />
  )
}

export default ReleasePipelineStatsTable
