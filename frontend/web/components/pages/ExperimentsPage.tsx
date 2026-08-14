import { FC, useCallback, useEffect, useState } from 'react'
import { useHistory } from 'react-router-dom'
import Utils from 'common/utils/utils'
import { useRouteContext } from 'components/providers/RouteContext'
import { useGetExperimentsQuery } from 'common/services/useExperiment'
import { useGetWarehouseConnectionsQuery } from 'common/services/useWarehouseConnection'
import { ExperimentStatus } from 'common/types/responses'
import useDebouncedSearch from 'common/useDebouncedSearch'
import Button from 'components/base/forms/Button'
import PageTitle from 'components/PageTitle'
import Paging from 'components/Paging'
import CreateExperimentWizard from 'components/experiments/CreateExperimentWizard'
import ExperimentsFakeDoor from 'components/experiments/ExperimentsFakeDoor'
import ExperimentsTable from 'components/experiments/ExperimentsTable'
import ExperimentsListControls from 'components/experiments/ExperimentsListControls'
import {
  FilterTab,
  TAB_LABELS,
  VISIBLE_TAB_ORDER,
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
      { environmentId: environmentId ?? '', exclude_event_stats: true },
      { skip: !environmentId },
    )

  const hasWarehouse = (warehouseConnections?.length ?? 0) > 0
  const experiments = experimentsData?.results
    ?.slice()
    ?.sort((a, b) => b.created_at.localeCompare(a.created_at))
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

  const hasExperiments = Utils.getFlagsmithHasFeature('experimental_flags')
  const hasFakeDoor = Utils.getFlagsmithHasFeature('experiments_fake_door')

  if (!Utils.isOrgOnFreePlan() && !hasExperiments && hasFakeDoor) {
    return (
      <div data-test='experiments-page' className='app-container container'>
        <PageTitle title='Experiments' />
        <ExperimentsFakeDoor />
      </div>
    )
  }

  if (!hasExperiments) {
    history.replace(
      `/project/${projectId}/environment/${environmentId}/features`,
    )
    return null
  }

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
    const tabs = VISIBLE_TAB_ORDER.map((value) => ({
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
            projectId={projectId}
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
            className='border-top-0'
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

  const renderCta = () => {
    if (isLoading || isLoadingWarehouse) {
      return undefined
    }
    if (hasWarehouse) {
      return (
        <Button onClick={() => setIsCreating(true)}>
          <Icon name='plus' width={16} />
          Create Experiment
        </Button>
      )
    }
    if (experimentCount > 0) {
      return (
        <Button theme='outline' onClick={() => history.push(settingsUrl)}>
          Connect Warehouse
        </Button>
      )
    }
    return undefined
  }

  return (
    <div data-test='experiments-page' className='app-container container'>
      <PageTitle title='Experiments' cta={renderCta()} />
      {renderBody()}
    </div>
  )
}

export default ExperimentsPage
