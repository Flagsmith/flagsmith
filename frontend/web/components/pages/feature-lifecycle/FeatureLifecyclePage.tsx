import React, { FC, useCallback, useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useRouteContext } from 'components/providers/RouteContext'
import { usePageTracking } from 'common/hooks/usePageTracking'
import { useProjectEnvironments } from 'common/hooks/useProjectEnvironments'
import { hasActiveFilters } from 'common/utils/featureFilterParams'
import PageTitle from 'components/PageTitle'
import Icon from 'components/Icon'
import Button from 'components/base/forms/Button'
import EnvironmentSelect from 'components/EnvironmentTagSelect'
import CreateFlagModal from 'components/modals/create-feature'
import LifecycleSidebar from './components/LifecycleSidebar'
import EvaluationChecker from './components/EvaluationChecker'
import NewSection from './components/NewSection'
import LiveSection from './components/LiveSection'
import PermanentSection from './components/PermanentSection'
import StaleSection from './components/StaleSection'
import MonitorSection from './components/MonitorSection'
import RemoveSection from './components/RemoveSection'
import { useLifecycleData } from './hooks/useLifecycleData'
import { useEvaluationCounts } from './hooks/useEvaluationCounts'
import {
  DEFAULT_FILTER_STATE,
  MONITOR_TOOLTIP,
  SECTIONS,
  STALE_TOOLTIP,
  buildPeriodOptions,
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
  const projectId = routeContext.projectId!
  const { environments } = useProjectEnvironments(projectId)
  const defaultEnvironmentApiKey = environments[0]?.api_key

  const allEnvironmentIds = useMemo(
    () => environments.map((e) => `${e.id}`),
    [environments],
  )
  const [selectedEnvironments, setSelectedEnvironments] = useState<string[]>([])

  useEffect(() => {
    if (allEnvironmentIds.length > 0 && selectedEnvironments.length === 0) {
      setSelectedEnvironments(allEnvironmentIds)
    }
  }, [allEnvironmentIds, selectedEnvironments.length])

  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTER_STATE)
  const handleFilterChange = useCallback(
    (updates: Partial<FilterState>) =>
      setFilters((prev) => ({ ...prev, ...updates })),
    [],
  )
  const clearFilters = useCallback(() => setFilters(DEFAULT_FILTER_STATE), [])
  const hasFilters = hasActiveFilters(filters)

  const section = useSectionParam()
  const activeSection = SECTIONS.find((s) => s.key === section)!

  const [monitorPeriod, setMonitorPeriod] = useState(1)
  const [removePeriod, setRemovePeriod] = useState(7)

  // Central data hook — 2 API calls, all filtering done here
  const {
    counts,
    error,
    isLoading,
    liveFlags,
    newFlags,
    permanentFlags,
    staleFlags,
    staleNoCodeFlags,
  } = useLifecycleData({
    environmentApiKey: defaultEnvironmentApiKey,
    filters,
    projectId,
  })

  // Monitor evaluation counts (short period — "has evaluation within")
  const {
    handleEvaluationResult: handleMonitorResult,
    isCheckingEvaluations: isCheckingMonitor,
    monitorCount,
    monitorFlags,
  } = useEvaluationCounts({
    period: monitorPeriod,
    selectedEnvironments,
    staleNoCodeFlags,
  })

  // Remove evaluation counts (longer period — "no evaluations in")
  const {
    handleEvaluationResult: handleRemoveResult,
    isCheckingEvaluations: isCheckingRemove,
    removeCount,
    removeFlags,
  } = useEvaluationCounts({
    period: removePeriod,
    selectedEnvironments,
    staleNoCodeFlags,
  })

  usePageTracking({
    context: {
      organisationId: routeContext.organisationId,
      projectId,
    },
    pageName: 'CLEANUP',
    saveToStorage: false,
  })

  if (!defaultEnvironmentApiKey) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  const filterProps = {
    filters,
    hasFilters,
    onClearFilters: clearFilters,
    onFilterChange: handleFilterChange,
    projectId,
  }

  const renderSection = () => {
    switch (section) {
      case 'new':
        return (
          <NewSection
            flags={newFlags}
            isLoading={isLoading}
            error={error}
            {...filterProps}
          />
        )
      case 'live':
        return (
          <LiveSection
            flags={liveFlags}
            isLoading={isLoading}
            error={error}
            {...filterProps}
          />
        )
      case 'permanent':
        return (
          <PermanentSection
            flags={permanentFlags}
            isLoading={isLoading}
            error={error}
            {...filterProps}
          />
        )
      case 'stale':
        return (
          <StaleSection
            flags={staleFlags}
            isLoading={isLoading}
            error={error}
            {...filterProps}
          />
        )
      case 'monitor':
        return (
          <MonitorSection
            flags={monitorFlags}
            isLoading={isLoading}
            isCheckingEvaluations={isCheckingMonitor}
            error={error}
            {...filterProps}
          />
        )
      case 'remove':
        return (
          <RemoveSection
            flags={removeFlags}
            isLoading={isLoading}
            isCheckingEvaluations={isCheckingRemove}
            error={error}
            {...filterProps}
          />
        )
      default:
        return null
    }
  }

  const activePeriod = section === 'monitor' ? monitorPeriod : removePeriod
  const setActivePeriod =
    section === 'monitor' ? setMonitorPeriod : setRemovePeriod
  const periodPrefix =
    section === 'monitor' ? 'Evaluated within' : 'No evaluations in'
  const periodOptions = buildPeriodOptions(periodPrefix)

  return (
    <div data-test='cleanup-page' id='cleanup-page'>
      {/* Hidden evaluators — monitor period */}
      {staleNoCodeFlags.map((flag) =>
        selectedEnvironments.map((envId) => (
          <EvaluationChecker
            key={`monitor-${
              flag.id
            }-${envId}-${monitorPeriod}-${selectedEnvironments.join()}`}
            featureId={flag.id}
            projectId={projectId}
            environmentId={envId}
            period={monitorPeriod}
            onResult={handleMonitorResult}
          />
        )),
      )}
      {/* Hidden evaluators — remove period */}
      {staleNoCodeFlags.map((flag) =>
        selectedEnvironments.map((envId) => (
          <EvaluationChecker
            key={`remove-${
              flag.id
            }-${envId}-${removePeriod}-${selectedEnvironments.join()}`}
            featureId={flag.id}
            projectId={projectId}
            environmentId={envId}
            period={removePeriod}
            onResult={handleRemoveResult}
          />
        )),
      )}
      <div className='d-md-flex'>
        <LifecycleSidebar
          projectId={projectId}
          activeSection={section}
          counts={counts}
          monitorCount={monitorCount}
          removeCount={removeCount}
          isLoading={isLoading}
          isCheckingMonitor={isCheckingMonitor}
          isCheckingRemove={isCheckingRemove}
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
                            environmentId={defaultEnvironmentApiKey}
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
                        className='d-inline-flex align-items-center gap-1'
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
            {(section === 'monitor' || section === 'remove') && (
              <>
                <div className='mb-3' style={{ maxWidth: 300 }}>
                  <Select
                    value={periodOptions.find((o) => o.value === activePeriod)}
                    onChange={(v: { value: number }) =>
                      setActivePeriod(v.value)
                    }
                    options={periodOptions}
                    className='react-select'
                  />
                </div>
                <div className='mb-3'>
                  <label className='fw-semibold mb-1 d-block'>
                    Environments
                  </label>
                  <EnvironmentSelect
                    projectId={projectId}
                    value={selectedEnvironments}
                    onChange={(v) =>
                      setSelectedEnvironments((v as string[]) || [])
                    }
                    idField='id'
                    multiple
                    allowEmpty
                  />
                </div>
              </>
            )}
            {renderSection()}
          </div>
        </div>
      </div>
    </div>
  )
}

export default FeatureLifecyclePage
