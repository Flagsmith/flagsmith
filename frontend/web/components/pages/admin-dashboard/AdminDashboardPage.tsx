import { FC, useState } from 'react'
import InstanceMetricsCards from './components/InstanceMetricsCards'
import OrganisationUsageTable from './components/OrganisationUsageTable'
import UsageTrendsChart from './components/UsageTrendsChart'
import ReleasePipelineStatsTable from './components/ReleasePipelineStatsTable'
import StaleFlagsTable from './components/StaleFlagsTable'
import IntegrationAdoptionTable from './components/IntegrationAdoptionTable'

import AccountStore from 'common/stores/account-store'
import Utils from 'common/utils/utils'
import { useGetAdminDashboardMetricsQuery } from 'common/services/useAdminDashboard'
import Button from 'components/base/forms/Button'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import ErrorMessage from 'components/ErrorMessage'

const AdminDashboardPage: FC = () => {
  const [days, setDays] = useState<30 | 60 | 90>(30)

  const { data, error, isLoading } = useGetAdminDashboardMetricsQuery({ days })

  // Security & feature flag check
  if (
    !Utils.getFlagsmithHasFeature('platform_hub')
  ) {
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
      <div className='mb-4 d-flex flex-row justify-content-between align-items-start'>
        <div>
          <h2>Platform Hub</h2>
          <p className='text-muted'>
            Centralised view of platform-wide usage, lifecycle, and adoption
            data
          </p>
        </div>
        <div className='d-flex gap-2'>
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
          <InstanceMetricsCards summary={data.summary} days={days} />

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
