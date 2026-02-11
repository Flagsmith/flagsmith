import { FC, useMemo, useState } from 'react'
import {
  IntegrationBreakdown,
  IntegrationData,
  OrganisationMetrics,
} from 'common/types/responses'
import { SortOrder } from 'common/types/requests'
import PanelSearch from 'components/PanelSearch'
import Icon from 'components/Icon'
import Utils from 'common/utils/utils'

type IntegrationScope = 'environment' | 'organisation' | 'project'

interface IntegrationAdoptionTableProps {
  data: IntegrationBreakdown[]
  organisations: OrganisationMetrics[]
  totalEnvironments: number
  totalOrganisations: number
  totalProjects: number
}

// Maps backend integration keys to their frontend display key.
// Keys not listed here map to themselves.
const BACKEND_TO_FRONTEND_KEY: Record<string, string> = {
  'grafana-project': 'grafana',
}

const toFrontendKey = (backendKey: string): string =>
  BACKEND_TO_FRONTEND_KEY[backendKey] ?? backendKey

type ScopeData = {
  counts: Record<number, number> // org_id → installation count
  scope: IntegrationScope
}

type OrgScopeDetail = {
  count: number
  denominator: number
  pct: number
  scope: IntegrationScope
}

type OrgDetail = {
  adopted: boolean
  organisation_id: number
  organisation_name: string
  scope_details: OrgScopeDetail[]
}

type AdoptionRow = {
  adoption_pct: number
  docs: string | undefined
  image: string
  integration_key: string
  org_count: number
  orgs: OrgDetail[]
  scopes: ScopeData[]
  title: string
}

const SCOPE_LABELS: Record<IntegrationScope, string> = {
  environment: 'environments',
  organisation: 'orgs',
  project: 'projects',
}

const orgDenominator = (
  scope: IntegrationScope,
  org: OrganisationMetrics,
): number => {
  if (scope === 'environment') return org.environment_count
  if (scope === 'project') return org.project_count
  return 1
}

const adoptionColour = (pct: number): string => {
  if (pct >= 70) return '#27AB95'
  if (pct >= 40) return '#FF9F43'
  return '#e74c3c'
}

const IntegrationAdoptionTable: FC<IntegrationAdoptionTableProps> = ({
  data,
  organisations,
  totalEnvironments,
  totalOrganisations,
  totalProjects,
}) => {
  const [expandedRows, setExpandedRows] = useState<string[]>([])

  const toggle = (key: string) => {
    setExpandedRows((prev) =>
      prev.includes(key) ? prev.filter((k) => k !== key) : [...prev, key],
    )
  }

  const rows = useMemo(() => {
    const integrationData = Utils.getIntegrationData() as Record<
      string,
      IntegrationData
    >

    // Group breakdown by frontend key → scope → per-org counts
    const byFrontendKey: Record<string, Record<string, ScopeData>> = {}

    data.forEach((item) => {
      const feKey = toFrontendKey(item.integration_type)
      const scope = item.scope as IntegrationScope
      if (!byFrontendKey[feKey]) {
        byFrontendKey[feKey] = {}
      }
      if (!byFrontendKey[feKey][scope]) {
        byFrontendKey[feKey][scope] = { counts: {}, scope }
      }
      const scopeData = byFrontendKey[feKey][scope]
      scopeData.counts[item.organisation_id] =
        (scopeData.counts[item.organisation_id] ?? 0) + item.count
    })

    // Build rows from all known frontend integrations
    const allKeys = new Set([
      ...Object.keys(byFrontendKey),
      ...Object.keys(integrationData),
    ])

    return Array.from(allKeys)
      .filter((key) => integrationData[key])
      .map((key): AdoptionRow => {
        const config = integrationData[key]
        const scopeMap = byFrontendKey[key] ?? {}
        const scopes = Object.values(scopeMap)

        // Unique orgs that have ANY scope of this integration
        const allOrgIds = new Set<number>()
        scopes.forEach((s) => {
          Object.keys(s.counts).forEach((id) => allOrgIds.add(Number(id)))
        })
        const orgCount = allOrgIds.size

        // Build per-org details
        const orgDetails: OrgDetail[] = organisations.map((org) => {
          const scopeDetails: OrgScopeDetail[] = scopes.map((s) => {
            const count = s.counts[org.id] ?? 0
            const denom = orgDenominator(s.scope, org)
            let pct: number
            if (s.scope === 'organisation') {
              pct = count > 0 ? 100 : 0
            } else {
              pct =
                denom > 0 ? Math.min(Math.round((count / denom) * 100), 100) : 0
            }
            return { count, denominator: denom, pct, scope: s.scope }
          })

          // For integrations with no backend data yet, show 0
          const adopted =
            scopes.length > 0 && scopeDetails.some((sd) => sd.count > 0)

          return {
            adopted,
            organisation_id: org.id,
            organisation_name: org.name,
            scope_details: scopeDetails,
          }
        })

        // Overall adoption: unique orgs / total orgs
        const adoptionPct =
          totalOrganisations > 0
            ? Math.round((orgCount / totalOrganisations) * 100)
            : 0

        return {
          adoption_pct: adoptionPct,
          docs: config.docs,
          image: config.image,
          integration_key: key,
          org_count: orgCount,
          orgs: orgDetails,
          scopes,
          title: config.title || key,
        }
      })
  }, [data, organisations, totalOrganisations])

  const totalForScope = (scope: IntegrationScope): number => {
    if (scope === 'organisation') return totalOrganisations
    if (scope === 'environment') return totalEnvironments
    return totalProjects
  }

  const isScopeFullCoverage = (detail: OrgScopeDetail): boolean => {
    if (detail.scope === 'organisation') return detail.count > 0
    return detail.count >= detail.denominator && detail.denominator > 0
  }

  const renderScopeLabel = (detail: OrgScopeDetail): string => {
    if (detail.scope === 'organisation') {
      return detail.count > 0 ? 'Organisation-level' : 'Not installed'
    }
    return `${detail.count} of ${detail.denominator} ${
      SCOPE_LABELS[detail.scope]
    }`
  }

  const renderOrgDetails = (row: AdoptionRow) => (
    <div style={{ background: '#fafbfc', borderTop: '1px solid #eee' }}>
      {row.orgs.map((org) => {
        const verified = org.scope_details.some(isScopeFullCoverage)

        return (
          <div
            key={org.organisation_id}
            className='d-flex flex-row align-items-center'
            style={{
              paddingBottom: 8,
              paddingLeft: 48,
              paddingRight: 20,
              paddingTop: 8,
            }}
          >
            <div
              className='flex-fill d-flex align-items-center'
              style={{ gap: 6 }}
            >
              <span className='font-weight-medium' style={{ fontSize: 13 }}>
                {org.organisation_name}
              </span>
              {verified && (
                <Icon fill='#27AB95' name='checkmark-circle' width={16} />
              )}
            </div>
            <div
              className='d-flex flex-column align-items-end'
              style={{ gap: 2, minWidth: 360 }}
            >
              {org.scope_details.map((detail) => (
                <div
                  key={detail.scope}
                  className='d-flex align-items-center'
                  style={{ gap: 8, width: '100%' }}
                >
                  <span
                    className='text-muted'
                    style={{ fontSize: 11, minWidth: 90, textAlign: 'right' }}
                  >
                    {SCOPE_LABELS[detail.scope]}
                  </span>
                  <div
                    style={{
                      background: '#e9ecef',
                      borderRadius: 4,
                      flex: 1,
                      height: 6,
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        background: adoptionColour(detail.pct),
                        borderRadius: 4,
                        height: '100%',
                        width: `${Math.max(
                          detail.pct,
                          detail.count > 0 ? 3 : 0,
                        )}%`,
                      }}
                    />
                  </div>
                  <span
                    className='text-muted'
                    style={{ fontSize: 11, minWidth: 120, textAlign: 'right' }}
                  >
                    {renderScopeLabel(detail)}
                  </span>
                </div>
              ))}
              {org.scope_details.length === 0 && (
                <span className='text-muted' style={{ fontSize: 12 }}>
                  Not installed
                </span>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )

  const renderBreakdownSummary = (row: AdoptionRow): string => {
    if (row.scopes.length === 0) {
      return `0 of ${totalOrganisations} orgs`
    }
    const parts = row.scopes.map((s) => {
      const total = totalForScope(s.scope)
      if (s.scope === 'organisation') {
        return `${Object.keys(s.counts).length} of ${total} ${
          SCOPE_LABELS[s.scope]
        }`
      }
      const installations = Object.values(s.counts).reduce(
        (sum, c) => sum + c,
        0,
      )
      return `${installations} of ${total} ${SCOPE_LABELS[s.scope]}`
    })
    return parts.join(', ')
  }

  return (
    <PanelSearch
      className='no-pad'
      filterRow={(item: AdoptionRow, search: string) =>
        item.title.toLowerCase().includes(search.toLowerCase())
      }
      header={
        <div className='table-header d-flex flex-row align-items-center'>
          <div className='table-column flex-fill' style={{ paddingLeft: 20 }}>
            Integration
          </div>
          <div className='table-column' style={{ width: 200 }}>
            Adoption
          </div>
          <div className='table-column' style={{ width: 200 }}>
            Breakdown
          </div>
        </div>
      }
      id='integration-adoption-table'
      items={rows}
      renderRow={(row: AdoptionRow) => {
        const hasAdoption = row.adoption_pct > 0
        const isExpanded =
          hasAdoption && expandedRows.includes(row.integration_key)

        return (
          <div>
            <div
              className={`flex-row list-item${hasAdoption ? ' clickable' : ''}`}
              onClick={
                hasAdoption ? () => toggle(row.integration_key) : undefined
              }
              style={{ paddingBottom: 12, paddingTop: 12 }}
            >
              <div
                className='flex-fill d-flex align-items-center gap-2 font-weight-medium'
                style={{ paddingLeft: 20 }}
              >
                {hasAdoption ? (
                  <Icon
                    name={isExpanded ? 'chevron-down' : 'chevron-right'}
                    width={16}
                  />
                ) : (
                  <div style={{ width: 16 }} />
                )}
                <img
                  alt={row.title}
                  src={row.image}
                  style={{ height: 24, width: 24 }}
                />
                {row.title}
                {row.docs && (
                  <a
                    className='fw-normal btn-link'
                    href={row.docs}
                    onClick={(e) => e.stopPropagation()}
                    rel='noopener noreferrer'
                    style={{ fontSize: 12 }}
                    target='_blank'
                  >
                    Docs{' '}
                    <Icon fill='#6837fc' name='open-external-link' width={12} />
                  </a>
                )}
              </div>
              <div
                className='table-column d-flex align-items-center'
                style={{ gap: 8, width: 200 }}
              >
                <div
                  style={{
                    background: '#e9ecef',
                    borderRadius: 4,
                    flex: 1,
                    height: 6,
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      background: adoptionColour(row.adoption_pct),
                      borderRadius: 4,
                      height: '100%',
                      width: `${Math.max(
                        row.adoption_pct,
                        row.org_count > 0 ? 3 : 0,
                      )}%`,
                    }}
                  />
                </div>
                <span
                  className='font-weight-medium'
                  style={{ fontSize: 13, minWidth: 36, textAlign: 'right' }}
                >
                  {row.adoption_pct}%
                </span>
              </div>
              <div
                className='table-column text-muted'
                style={{ fontSize: 13, width: 200 }}
              >
                {renderBreakdownSummary(row)}
              </div>
            </div>
            {isExpanded && renderOrgDetails(row)}
          </div>
        )
      }}
      sorting={[
        {
          default: true,
          label: 'Adoption',
          order: SortOrder.DESC,
          value: 'adoption_pct',
        },
        {
          label: 'Name',
          order: SortOrder.ASC,
          value: 'title',
        },
      ]}
      title='Integration Adoption'
    />
  )
}

export default IntegrationAdoptionTable
