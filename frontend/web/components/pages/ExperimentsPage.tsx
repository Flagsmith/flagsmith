import { FC, useCallback, useEffect, useState } from 'react'
import { useHistory } from 'react-router-dom'
import { useRouteContext } from 'components/providers/RouteContext'
import { useGetExperimentsQuery } from 'common/services/useExperiment'
import { useGetWarehouseConnectionsQuery } from 'common/services/useWarehouseConnection'
import { ExperimentStatus } from 'common/types/responses'
import useDebouncedSearch from 'common/useDebouncedSearch'
import Button from 'components/base/forms/Button'
import PageTitle from 'components/PageTitle'
import Paging from 'components/Paging'
import CreateExperimentWizard from 'components/experiments/CreateExperimentWizard'
import ExperimentsTable from 'components/experiments/ExperimentsTable'
import ExperimentsListControls from 'components/experiments/ExperimentsListControls'
import {
  FilterTab,
  TAB_LABELS,
  TAB_ORDER,
} from 'components/experiments/constants'
import Icon from 'components/icons/Icon'

const PAGE_SIZE = 10

const ExperimentsPage: FC = () => {
  const { environmentId, projectId } = useRouteContext()
  const [isCreating, setIsCreating] = useState(false)
  const [activeTab, setActiveTab] = useState<FilterTab>('all')
  const [page, setPage] = useState(1)
  const { search, searchInput, setSearchInput } = useDebouncedSearch()
  const history = useHistory()

  useEffect(() => {
    setPage(1)
  }, [activeTab, search])

  useEffect(() => {
    setIsCreating(false)
  }, [environmentId])

  const { data: experimentsData, isLoading } = useGetExperimentsQuery(
    {
      environmentId: environmentId ?? '',
      page,
      page_size: PAGE_SIZE,
      q: search || undefined,
      status: activeTab !== 'all' ? activeTab : undefined,
    },
    { skip: !environmentId },
  )

  const { data: warehouseConnections, isLoading: isLoadingWarehouse } =
    useGetWarehouseConnectionsQuery(
      { environmentId: environmentId ?? '' },
      { skip: !environmentId },
    )

  const hasWarehouse = (warehouseConnections?.length ?? 0) > 0
  const experiments = experimentsData?.results
  const experimentCount = experimentsData?.count ?? 0
  const statusCounts = experimentsData?.status_counts

  const getTabLabel = useCallback(
    (tab: FilterTab) => {
      const label = TAB_LABELS[tab]
      if (!statusCounts) return label
      if (tab === 'all') {
        const total = Object.values(statusCounts).reduce(
          (a, b) => a + (b ?? 0),
          0,
        )
        return total > 0 ? `${label} (${total})` : label
      }
      const count = statusCounts[tab as ExperimentStatus] ?? 0
      return count > 0 ? `${label} (${count})` : label
    },
    [statusCounts],
  )

  if (!environmentId || !projectId) return null

  if (isCreating) {
    return (
      <div data-test='experiments-page' className='app-container container'>
        <PageTitle
          title='Create Experiment'
          cta={
            <Button theme='outline' onClick={() => setIsCreating(false)}>
              Cancel
            </Button>
          }
        />
        <CreateExperimentWizard
          environmentId={environmentId}
          projectId={projectId}
          onCreated={() => setIsCreating(false)}
        />
      </div>
    )
  }

  const hasActiveFilter = activeTab !== 'all' || !!search
  const settingsUrl = `/project/${projectId}/environment/${environmentId}/settings?tab=warehouse`

  const renderBody = () => {
    if (isLoading || isLoadingWarehouse) {
      return (
        <div className='text-center'>
          <Loader />
        </div>
      )
    }
    if (!hasWarehouse && experimentCount === 0 && !hasActiveFilter) {
      return (
        <div className='text-center py-5'>
          <Icon
            name='setting'
            width={48}
            className='text-muted mb-3 d-block mx-auto'
          />
          <h5>Data warehouse not configured</h5>
          <p className='text-muted mb-4'>
            Experiments require a data warehouse connection to collect and
            analyse results. Configure one in your environment settings to get
            started.
          </p>
          <Button onClick={() => history.push(settingsUrl)}>
            Configure Warehouse
          </Button>
        </div>
      )
    }
    if (experimentCount === 0 && !hasActiveFilter) {
      return (
        <div className='text-center py-5'>
          <Icon
            name='flask'
            width={48}
            className='text-muted mb-3 d-block mx-auto'
          />
          <h5>No experiments yet</h5>
          <p className='text-muted mb-4'>
            Create your first experiment to start testing hypotheses with your
            feature flags.
          </p>
          <Button onClick={() => setIsCreating(true)}>
            <Icon name='plus' width={16} />
            Create Experiment
          </Button>
        </div>
      )
    }
    const tabs = TAB_ORDER.map((value) => ({
      label: getTabLabel(value),
      value,
    }))
    const hasResults = !!experiments?.length
    return (
      <>
        <ExperimentsListControls
          tabs={tabs}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          searchInput={searchInput}
          onSearchChange={setSearchInput}
        />
        {hasResults ? (
          <ExperimentsTable
            experiments={experiments}
            environmentId={environmentId}
          />
        ) : (
          <div className='text-center py-5'>
            <p className='text-muted'>
              No experiments match your {search ? 'search' : 'filter'}.
            </p>
          </div>
        )}
        {hasResults && (
          <Paging
            paging={{
              ...(experimentsData || {}),
              page,
              pageSize: PAGE_SIZE,
            }}
            nextPage={() => setPage(page + 1)}
            prevPage={() => setPage(page - 1)}
            goToPage={(p: number) => setPage(p)}
            isLoading={isLoading}
          />
        )}
      </>
    )
  }

  return (
    <div data-test='experiments-page' className='app-container container'>
      <PageTitle
        title='Experiments'
        cta={
          hasWarehouse ? (
            <Button onClick={() => setIsCreating(true)}>
              <Icon name='plus' width={16} />
              Create Experiment
            </Button>
          ) : undefined
        }
      />
      {renderBody()}
    </div>
  )
}

export default ExperimentsPage
