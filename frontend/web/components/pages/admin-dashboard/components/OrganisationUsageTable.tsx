import { FC, useState } from 'react'
import { OrganisationMetrics, ProjectMetrics } from 'common/types/responses'
import { SortOrder } from 'common/types/requests'
import Utils from 'common/utils/utils'
import PanelSearch from 'components/PanelSearch'
import Icon from 'components/icons/Icon'
import Text from 'components/base/Text'

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
              <Text variant='b2' className='text-muted'>
                {env.name}
              </Text>
            </div>
            <div style={{ width: 120 }} />
            <div style={{ width: 120 }} />
            <Text
              variant='b2'
              as='div'
              className='table-column text-muted'
              style={{ width: 160 }}
            >
              {Utils.numberWithCommas(env.api_calls_30d)}
            </Text>
            <Text
              variant='b2'
              as='div'
              className='table-column text-muted'
              style={{ width: 140 }}
            >
              {envPct}% of org usage
            </Text>
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
                  <Text variant='b2' className='font-weight-medium'>
                    {project.name}
                  </Text>
                  <Text variant='b3' className='text-muted'>
                    ({project.environments.length} environments)
                  </Text>
                </div>
                <Text
                  variant='b2'
                  as='div'
                  className='table-column text-muted'
                  style={{ width: 120 }}
                >
                  {project.flags}
                </Text>
                <div style={{ width: 120 }} />
                <Text
                  variant='b2'
                  as='div'
                  className='table-column text-muted'
                  style={{ width: 160 }}
                >
                  {Utils.numberWithCommas(project.api_calls_30d)}
                </Text>
                <Text
                  variant='b2'
                  as='div'
                  className='table-column text-muted'
                  style={{ width: 140 }}
                >
                  {projectPct}% of org usage
                </Text>
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
                <Text variant='b2' as='div' className='text-muted'>
                  {Utils.numberWithCommas(org.active_users_30d)} active users
                </Text>
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
                <Text variant='b3' as='div' className='text-muted'>
                  {Utils.numberWithCommas(org.stale_flags)} stale
                </Text>
              )}
            </div>
            <div
              className='table-column d-flex flex-column align-items-start'
              style={{ width: 120 }}
            >
              <div className='font-weight-medium'>
                {Utils.numberWithCommas(org.total_users)}
              </div>
              <Text variant='b3' as='div' className='text-muted'>
                {Utils.numberWithCommas(org.active_users_30d)} active
              </Text>
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
            <Text
              variant='b2'
              as='div'
              className='table-column'
              style={{ width: 140 }}
            >
              {overageCell(
                org[
                  `api_calls_${days}d` as keyof OrganisationMetrics
                ] as number,
                org.api_calls_allowed * (days / 30),
              )}
            </Text>
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
