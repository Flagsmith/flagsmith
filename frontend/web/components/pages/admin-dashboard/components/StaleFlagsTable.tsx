import { FC } from 'react'
import { StaleFlagsPerProject } from 'common/types/responses'
import { SortOrder } from 'common/types/requests'
import PanelSearch from 'components/PanelSearch'

interface StaleFlagsTableProps {
  data: StaleFlagsPerProject[]
}

const StaleFlagsTable: FC<StaleFlagsTableProps> = ({ data }) => {
  return (
    <PanelSearch
      className='no-pad'
      filterRow={(item: StaleFlagsPerProject, search: string) =>
        item.organisation_name.toLowerCase().includes(search.toLowerCase()) ||
        item.project_name.toLowerCase().includes(search.toLowerCase())
      }
      header={
        <div className='table-header d-flex flex-row align-items-center'>
          <div className='table-column flex-fill' style={{ paddingLeft: 20 }}>
            Organisation / Project
          </div>
          <div className='table-column' style={{ width: 120 }}>
            Stale Flags
          </div>
          <div className='table-column' style={{ width: 120 }}>
            Total Flags
          </div>
          <div className='table-column' style={{ width: 100 }}>
            % Stale
          </div>
        </div>
      }
      id='stale-flags-table'
      items={data}
      paging={data.length > 10 ? { goToPage: 1, pageSize: 10 } : undefined}
      renderRow={(row: StaleFlagsPerProject) => (
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
          <div
            className='table-column font-weight-medium'
            style={{ width: 120 }}
          >
            {row.stale_flags}
          </div>
          <div
            className='table-column font-weight-medium'
            style={{ width: 120 }}
          >
            {row.total_flags}
          </div>
          <div
            className='table-column font-weight-medium'
            style={{ width: 100 }}
          >
            {row.total_flags > 0
              ? `${Math.round((row.stale_flags / row.total_flags) * 100)}%`
              : '0%'}
          </div>
        </div>
      )}
      sorting={[
        {
          default: true,
          label: 'Stale Flags',
          order: SortOrder.DESC,
          value: 'stale_flags',
        },
        {
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
      title='Stale Flags per Project'
    />
  )
}

export default StaleFlagsTable
