import React, { FC, useCallback, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useRouteContext } from 'components/providers/RouteContext'
import { usePageTracking } from 'common/hooks/usePageTracking'
import { hasActiveFilters } from 'common/utils/featureFilterParams'
import PageTitle from 'components/PageTitle'
import Icon from 'components/icons/Icon'
import Button from 'components/base/forms/Button'
import CreateFlagModal from 'components/modals/create-feature'
import LifecycleSidebar from './components/LifecycleSidebar'
import FeatureUsageModal from './components/FeatureUsageModal'
import NewSection from './components/NewSection'
import LiveSection from './components/LiveSection'
import PermanentSection from './components/PermanentSection'
import StaleSection from './components/StaleSection'
import MonitorSection from './components/MonitorSection'
import RemoveSection from './components/RemoveSection'
import type { ProjectFlag } from 'common/types/responses'
import { useLifecycleEnvironment } from './hooks/useLifecycleEnvironment'
import {
  useLifecycleCounts,
  useLifecycleSectionFlags,
} from './hooks/useLifecycleData'
import {
  DEFAULT_FILTER_STATE,
  MONITOR_TOOLTIP,
  SECTIONS,
  STALE_TOOLTIP,
} from './constants'
import type { Section } from './types'
import type { FilterState } from 'common/types/featureFilters'

function useSectionParam(): Section {
  const { section } = useParams<{ section?: string }>()
  return useMemo(() => {
    const valid: Section[] = [
      'new',
      'live',
      'permanent',
      'stale',
      'monitor',
      'remove',
    ]
    return valid.includes(section as Section) ? (section as Section) : 'new'
  }, [section])
}

const FeatureLifecyclePage: FC = () => {
  const routeContext = useRouteContext()
  const projectId = String(routeContext.projectId)
  const projectIdNum = Number(projectId)

  const { environmentId, setEnvironmentId } =
    useLifecycleEnvironment(projectIdNum)

  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTER_STATE)
  const handleFilterChange = useCallback(
    (updates: Partial<FilterState>) =>
      setFilters((prev) => ({ ...prev, ...updates })),
    [],
  )
  const clearFilters = useCallback(() => setFilters(DEFAULT_FILTER_STATE), [])

  const handleFeatureClick = useCallback(
    (flag: ProjectFlag) => {
      openModal(
        flag.name,
        <FeatureUsageModal
          projectId={projectIdNum}
          environmentId={environmentId}
          projectFlag={flag}
        />,
        'side-modal create-feature-modal',
      )
    },
    [projectIdNum, environmentId],
  )
  const hasFilters = hasActiveFilters(filters)

  const section = useSectionParam()
  const activeSection = SECTIONS.find(
    (s) => s.key === section,
  ) as (typeof SECTIONS)[number]

  const { counts, isLoading: isLoadingCounts } = useLifecycleCounts({
    environmentId,
  })

  const {
    error,
    flags,
    isLoading: isLoadingFlags,
  } = useLifecycleSectionFlags({
    environmentId,
    filters,
    projectId: projectIdNum,
    section,
  })

  usePageTracking({
    context: {
      organisationId: routeContext.organisationId,
      projectId: projectIdNum,
    },
    pageName: 'CLEANUP',
    saveToStorage: false,
  })

  if (!environmentId) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  const filterProps = {
    error,
    filters,
    flags,
    hasFilters,
    isLoading: isLoadingFlags,
    onClearFilters: clearFilters,
    onFeatureClick: handleFeatureClick,
    onFilterChange: handleFilterChange,
    projectId: projectIdNum,
  }

  const renderSection = () => {
    switch (section) {
      case 'new':
        return <NewSection {...filterProps} />
      case 'live':
        return <LiveSection {...filterProps} />
      case 'permanent':
        return <PermanentSection {...filterProps} />
      case 'stale':
        return <StaleSection {...filterProps} />
      case 'monitor':
        return <MonitorSection {...filterProps} />
      case 'remove':
        return <RemoveSection {...filterProps} />
      default:
        return null
    }
  }

  return (
    <div data-test='cleanup-page' id='cleanup-page'>
      <div className='d-md-flex'>
        <LifecycleSidebar
          projectId={projectIdNum}
          activeSection={section}
          counts={counts}
          isLoading={isLoadingCounts}
          environmentId={environmentId}
          onEnvironmentChange={setEnvironmentId}
        />
        <div className='aside-container'>
          <div className='app-container container'>
            <div className=' mb-0'>
              <PageTitle
                title={`${activeSection.label} Features`}
                cta={
                  section === 'new' ? (
                    <Button
                      onClick={() => {
                        openModal(
                          'New Feature',
                          <CreateFlagModal
                            environmentId={`${environmentId}`}
                            projectId={projectId}
                          />,
                          'side-modal create-feature-modal',
                        )
                      }}
                      data-test='create-feature-btn'
                    >
                      Create Feature
                    </Button>
                  ) : undefined
                }
              >
                {activeSection.subtitle}
                {activeSection.staleTooltip && (
                  <Tooltip
                    title={
                      <span className='d-inline-flex align-items-center gap-1'>
                        What is stale? <Icon name='info-outlined' width={16} />
                      </span>
                    }
                  >
                    {STALE_TOOLTIP}
                  </Tooltip>
                )}
                {activeSection.monitorTooltip && (
                  <Tooltip
                    title={
                      <a
                        className='ms-1 d-inline-flex align-items-center gap-1'
                        href='#'
                        onClick={(e) => e.preventDefault()}
                      >
                        Why am I seeing this?
                      </a>
                    }
                  >
                    {MONITOR_TOOLTIP}
                  </Tooltip>
                )}
              </PageTitle>
            </div>
            {renderSection()}
          </div>
        </div>
      </div>
    </div>
  )
}

export default FeatureLifecyclePage
