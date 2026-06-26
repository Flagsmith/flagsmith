import { useMemo } from 'react'
import { useGetExperimentsQuery } from 'common/services/useExperiment'
import type { Experiment } from 'common/types/responses'

export type FeatureExperimentFreeze = {
  isFrozen: boolean
  experiment: Experiment | null
  isLoading: boolean
}

export function useFeatureExperimentFreeze(
  featureId: number | undefined,
  environmentId: string,
): FeatureExperimentFreeze {
  const skip = !featureId
  const { data: runningData, isLoading: loadingRunning } =
    useGetExperimentsQuery({ environmentId, status: 'running' }, { skip })
  const { data: pausedData, isLoading: loadingPaused } = useGetExperimentsQuery(
    { environmentId, status: 'paused' },
    { skip },
  )

  const isLoading = loadingRunning || loadingPaused

  const experiment = useMemo(() => {
    if (!featureId) return null
    const all = [
      ...(runningData?.results ?? []),
      ...(pausedData?.results ?? []),
    ]
    return all.find((e) => e.feature?.id === featureId) ?? null
  }, [runningData?.results, pausedData?.results, featureId])

  return {
    experiment,
    isFrozen: experiment !== null,
    isLoading,
  }
}
