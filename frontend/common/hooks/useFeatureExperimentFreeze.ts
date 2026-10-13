import { useMemo } from 'react'
import { useGetExperimentsQuery } from 'common/services/useExperiment'
import type { Experiment } from 'common/types/responses'
import { useHasExperimentationFeature } from './useHasExperimentationFeature'

export type FeatureExperimentFreeze = {
  isFrozen: boolean
  experiment: Experiment | null
  isLoading: boolean
}

export function useFeatureExperimentFreeze(
  featureId: number | undefined,
  environmentId: string,
): FeatureExperimentFreeze {
  const { enabled: isExperimentEnabled } =
    useHasExperimentationFeature('experimental_flags')
  const skip = !isExperimentEnabled || !featureId || !environmentId
  const { data, isLoading } = useGetExperimentsQuery(
    { environmentId, status: 'running' },
    { skip },
  )

  const experiment = useMemo(() => {
    if (!featureId || !data?.results) return null
    return data.results.find((e) => e.feature?.id === featureId) ?? null
  }, [data?.results, featureId])

  return {
    experiment,
    isFrozen: experiment !== null,
    isLoading,
  }
}
