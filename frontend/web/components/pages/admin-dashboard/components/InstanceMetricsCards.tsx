import { FC } from 'react'
import StatItem from 'components/StatItem'

interface InstanceMetricsCardsProps {
  summary: {
    total_organisations: number
    total_flags: number
    total_users: number
    total_api_calls_30d: number
    active_organisations: number
    total_projects: number
    total_environments: number
    total_integrations: number
    active_users: number
  }
  days?: number
}

const InstanceMetricsCards: FC<InstanceMetricsCardsProps> = ({
  days = 30,
  summary,
}) => {
  return (
    <div
      className='d-flex flex-row justify-content-between mb-4'
      style={{ gap: '24px' }}
    >
      <div className='flex-fill'>
        <StatItem
          icon='layers'
          label='Organisations'
          value={summary.total_organisations}
        />
        <small className='text-muted d-block mt-1'>
          {summary.active_organisations} active in last {days} days
        </small>
      </div>

      <div className='flex-fill'>
        <StatItem
          icon='features'
          label='Total Flags'
          value={summary.total_flags}
        />
        <small className='text-muted d-block mt-1'>
          Across {summary.total_projects} projects
        </small>
      </div>

      <div className='flex-fill'>
        <StatItem icon='people' label='Seats' value={summary.total_users} />
        <small className='text-muted d-block mt-1'>
          {summary.active_users} active of {summary.total_users}
        </small>
      </div>

      <div className='flex-fill'>
        <StatItem
          icon='bar-chart'
          label='API Calls'
          value={summary.total_api_calls_30d}
        />
        <small className='text-muted d-block mt-1'>
          Across {summary.total_environments} environments
        </small>
      </div>

      <div className='flex-fill'>
        <StatItem
          icon='options-2'
          label='Integrations'
          value={summary.total_integrations}
        />
        <small className='text-muted d-block mt-1'>
          Across {summary.total_organisations} organisations
        </small>
      </div>
    </div>
  )
}

export default InstanceMetricsCards
