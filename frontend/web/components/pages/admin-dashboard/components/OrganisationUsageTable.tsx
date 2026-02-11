import { FC, useState } from 'react'
import { OrganisationMetrics, ProjectMetrics } from 'common/types/responses'
import { SortOrder } from 'common/types/requests'
import Utils from 'common/utils/utils'
import PanelSearch from 'components/PanelSearch'
import Icon from 'components/Icon'

interface OrganisationUsageTableProps {
  days: 30 | 60 | 90
  organisations: OrganisationMetrics[]
}

const overageCell = (apiCalls: number, allowed: number) => {
  if (allowed === 0) {
    return <span className='text-muted'>—</span>
  }
  const diff = apiCalls - allowed
  const pct = Math.round((diff / allowed) * 100)
  if (diff > 0) {
    return (
      <span style={{ color: '#e74c3c', fontWeight: 600 }}>
        +{pct}% (+{Utils.numberWithCommas(diff)})
      </span>
    )
  }
  return (
    <span style={{ color: '#27AB95', fontWeight: 600 }}>
      {pct}% (-{Utils.numberWithCommas(Math.abs(diff))})
    </span>
  )
}

const OrganisationUsageTable: FC<OrganisationUsageTableProps> = ({
  days,
  organisations,
}) => {
  const [expandedOrgs, setExpandedOrgs] = useState<number[]>([])
  const [expandedProjects, setExpandedProjects] = useState<number[]>([])

  const toggleOrg = (id: number) => {
    setExpandedOrgs((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    )
  }

  const toggleProject = (id: number) => {
    setExpandedProjects((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id],
    )
  }

  const renderEnvironments = (project: ProjectMetrics, orgApiCalls: number) => (
    <div style={{ background: '#f8f9fa', borderTop: '1px solid #eee' }}>
      {project.environments.map((env) => {
        const envPct =
          orgApiCalls > 0
            ? Math.round((env.api_calls_30d / orgApiCalls) * 100)
            : 0
        return (
          <div
            key={env.id}
            className='d-flex flex-row align-items-center'
            style={{ paddingBottom: 8, paddingLeft: 80, paddingTop: 8 }}
          >
            <div className='flex-fill'>
              <span className='text-muted' style={{ fontSize: 13 }}>
                {env.name}
              </span>
            </div>
            <div style={{ width: 120 }} />
            <div style={{ width: 120 }} />
            <div
              className='table-column text-muted'
              style={{ fontSize: 13, width: 160 }}
            >
              {Utils.numberWithCommas(env.api_calls_30d)}
            </div>
            <div
              className='table-column text-muted'
              style={{ fontSize: 13, width: 140 }}
            >
              {envPct}% of org usage
            </div>
          </div>
        )
      })}
    </div>
  )

  const renderProjects = (org: OrganisationMetrics) => {
    const orgApiCalls = org.api_calls_30d
    return (
      <div style={{ background: '#fafbfc', borderTop: '1px solid #eee' }}>
        {org.projects.map((project) => {
          const projectPct =
            orgApiCalls > 0
              ? Math.round((project.api_calls_30d / orgApiCalls) * 100)
              : 0
          return (
            <div key={project.id}>
              <div
                className='d-flex flex-row align-items-center clickable'
                onClick={() => toggleProject(project.id)}
                style={{ paddingBottom: 10, paddingLeft: 48, paddingTop: 10 }}
              >
                <div
                  className='flex-fill d-flex align-items-center'
                  style={{ gap: 6 }}
                >
                  <Icon
                    name={
                      expandedProjects.includes(project.id)
                        ? 'chevron-down'
                        : 'chevron-right'
                    }
                    width={14}
                  />
                  <span className='font-weight-medium' style={{ fontSize: 13 }}>
                    {project.name}
                  </span>
                  <span className='text-muted' style={{ fontSize: 12 }}>
                    ({project.environments.length} environments)
                  </span>
                </div>
                <div
                  className='table-column text-muted'
                  style={{ fontSize: 13, width: 120 }}
                >
                  {project.flags}
                </div>
                <div style={{ width: 120 }} />
                <div
                  className='table-column text-muted'
                  style={{ fontSize: 13, width: 160 }}
                >
                  {Utils.numberWithCommas(project.api_calls_30d)}
                </div>
                <div
                  className='table-column text-muted'
                  style={{ fontSize: 13, width: 140 }}
                >
                  {projectPct}% of org usage
                </div>
              </div>
              {expandedProjects.includes(project.id) &&
                renderEnvironments(project, orgApiCalls)}
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <PanelSearch
      className='no-pad'
      filterRow={(item: OrganisationMetrics, search: string) =>
        item.name.toLowerCase().includes(search.toLowerCase())
      }
      header={
        <div className='table-header d-flex flex-row align-items-center'>
          <div className='table-column flex-fill' style={{ paddingLeft: 20 }}>
            Organisation
          </div>
          <div className='table-column' style={{ width: 120 }}>
            Flags
          </div>
          <div className='table-column' style={{ width: 120 }}>
            Seats
          </div>
          <div className='table-column' style={{ width: 160 }}>
            API Calls ({days}d)
          </div>
          <div className='table-column' style={{ width: 140 }}>
            Overage ({days}d)
          </div>
        </div>
      }
      id='organisation-usage-table'
      items={organisations}
      paging={
        organisations.length > 10 ? { goToPage: 1, pageSize: 10 } : undefined
      }
      renderRow={(org: OrganisationMetrics) => (
        <div>
          <div
            className='flex-row list-item clickable'
            onClick={() => toggleOrg(org.id)}
            style={{ paddingBottom: 12, paddingTop: 12 }}
          >
            <div
              className='flex-fill d-flex align-items-center'
              style={{ gap: 8, paddingLeft: 20 }}
            >
              <Icon
                name={
                  expandedOrgs.includes(org.id)
                    ? 'chevron-down'
                    : 'chevron-right'
                }
                width={16}
              />
              <div>
                <div className='font-weight-medium mb-1'>{org.name}</div>
                <div className='text-muted' style={{ fontSize: 13 }}>
                  {Utils.numberWithCommas(org.active_users_30d)} active users
                </div>
              </div>
            </div>
            <div
              className='table-column d-flex flex-column align-items-start'
              style={{ width: 120 }}
            >
              <div className='font-weight-medium'>
                {Utils.numberWithCommas(org.total_flags)}
              </div>
              {org.stale_flags > 0 && (
                <div className='text-muted' style={{ fontSize: 12 }}>
                  {Utils.numberWithCommas(org.stale_flags)} stale
                </div>
              )}
            </div>
            <div
              className='table-column d-flex flex-column align-items-start'
              style={{ width: 120 }}
            >
              <div className='font-weight-medium'>
                {Utils.numberWithCommas(org.total_users)}
              </div>
              <div className='text-muted' style={{ fontSize: 12 }}>
                {Utils.numberWithCommas(org.active_users_30d)} active
              </div>
            </div>
            <div
              className='table-column font-weight-medium'
              style={{ width: 160 }}
            >
              {Utils.numberWithCommas(
                org[
                `api_calls_${days}d` as keyof OrganisationMetrics
                ] as number,
              )}
            </div>
            <div className='table-column' style={{ fontSize: 13, width: 140 }}>
              {overageCell(
                org[
                `api_calls_${days}d` as keyof OrganisationMetrics
                ] as number,
                org.api_calls_allowed * (days / 30),
              )}
            </div>
          </div>
          {expandedOrgs.includes(org.id) && renderProjects(org)}
        </div>
      )}
      sorting={[
        {
          default: true,
          label: 'Name',
          order: SortOrder.ASC,
          value: 'name',
        },
        {
          label: 'API Calls',
          order: SortOrder.DESC,
          value: `api_calls_${days}d`,
        },
        {
          label: 'Overage',
          order: SortOrder.DESC,
          value: `overage_${days}d`,
        },
        { label: 'Flags', order: SortOrder.DESC, value: 'total_flags' },
        { label: 'Seats', order: SortOrder.DESC, value: 'total_users' },
      ]}
      title='Organisations'
    />
  )
}

export default OrganisationUsageTable
