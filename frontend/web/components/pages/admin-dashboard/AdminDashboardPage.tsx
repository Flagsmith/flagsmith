import { FC, useEffect, useRef, useState } from 'react'
import InstanceMetricsCards from './components/InstanceMetricsCards'
import OrganisationUsageTable from './components/OrganisationUsageTable'
import UsageTrendsChart from './components/UsageTrendsChart'
import ReleasePipelineStatsTable from './components/ReleasePipelineStatsTable'
import StaleFlagsTable from './components/StaleFlagsTable'
import IntegrationAdoptionTable from './components/IntegrationAdoptionTable'

import Utils from 'common/utils/utils'
import { useGetAdminDashboardMetricsQuery } from 'common/services/useAdminDashboard'
import Button from 'components/base/forms/Button'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import ErrorMessage from 'components/ErrorMessage'

const AdminDashboardPage: FC = () => {
  const [days, setDays] = useState<30 | 60 | 90>(30)
  const [isStuck, setIsStuck] = useState(false)
  const sentinelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = sentinelRef.current
    if (!el) return
    const observer = new IntersectionObserver(
      ([entry]) => setIsStuck(!entry.isIntersecting),
      { threshold: 0 },
    )
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  const isEnabled = Utils.getFlagsmithHasFeature('platform_hub')
  const { data, error, isLoading } = useGetAdminDashboardMetricsQuery(
    { days },
    { skip: !isEnabled },
  )

  if (!isEnabled) {
    return (
      <div className='app-container text-center py-5'>
        <h3>Access Denied</h3>
        <p className='text-muted'>
          This page is only accessible to instance administrators.
        </p>
      </div>
    )
  }

  return (
    <div className='app-container container'>
      <div className='py-2' style={{ marginBottom: -48 }}>
        <h2 className='mb-0'>Platform Hub</h2>
        <p className='text-muted mb-0'>
          Centralised view of platform-wide usage, lifecycle, and adoption data
        </p>
      </div>
      <div ref={sentinelRef} />
      <div
        className='d-flex justify-content-end mb-2'
        style={{
          minHeight: 48,
          position: 'sticky',
          top: 0,
          zIndex: 10,
        }}
      >
        <div
          className='d-flex gap-2 align-items-center'
          style={{
            background: isStuck ? 'var(--body-bg, #fff)' : 'transparent',
            borderRadius: isStuck ? '0 0 8px 8px' : 0,
            boxShadow: isStuck ? '0 4px 8px rgba(0,0,0,0.12)' : 'none',
            padding: '8px 16px',
            transition: 'background 0.2s, box-shadow 0.2s, border-radius 0.2s',
          }}
        >
          <Button
            onClick={() => setDays(30)}
            className={days === 30 ? 'btn-primary' : 'btn-secondary'}
            size='small'
          >
            30 days
          </Button>
          <Button
            onClick={() => setDays(60)}
            className={days === 60 ? 'btn-primary' : 'btn-secondary'}
            size='small'
          >
            60 days
          </Button>
          <Button
            onClick={() => setDays(90)}
            className={days === 90 ? 'btn-primary' : 'btn-secondary'}
            size='small'
          >
            90 days
          </Button>
        </div>
      </div>

      {isLoading && (
        <div className='centered-container'>
          <Loader />
        </div>
      )}

      <ErrorMessage>{error}</ErrorMessage>

      {data && (
        <>
          {/* KPI Cards — always visible */}
          <div className='mt-3'>
            <InstanceMetricsCards summary={data.summary} days={days} />
          </div>

          {/* Tabbed sections */}
          <Tabs urlParam='tab' uncontrolled>
            <TabItem tabLabel='Usage'>
              <div className='mt-4'>
                <div className='mb-4'>
                  <UsageTrendsChart trends={data.usage_trends} days={days} />
                </div>
                <OrganisationUsageTable
                  days={days}
                  organisations={data.organisations}
                />
              </div>
            </TabItem>

            <TabItem tabLabel='Release Pipeline'>
              <div className='mt-4'>
                <ReleasePipelineStatsTable
                  stats={data.release_pipeline_stats}
                  totalProjects={data.summary.total_projects}
                />
              </div>
            </TabItem>

            <TabItem tabLabel='Flag Lifecycle'>
              <div className='mt-4'>
                <StaleFlagsTable data={data.stale_flags_per_project} />
              </div>
            </TabItem>

            <TabItem tabLabel='Integrations'>
              <div className='mt-4'>
                <IntegrationAdoptionTable
                  data={data.integration_breakdown}
                  organisations={data.organisations}
                  totalEnvironments={data.summary.total_environments}
                  totalOrganisations={data.summary.total_organisations}
                  totalProjects={data.summary.total_projects}
                />
              </div>
            </TabItem>
          </Tabs>
        </>
      )}
    </div>
  )
}

export default AdminDashboardPage
