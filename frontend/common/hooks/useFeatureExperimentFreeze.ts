import { useMemo } from 'react'
import { useGetExperimentsQuery } from 'common/services/useExperiment'
import type { Experiment } from 'common/types/responses'
import Utils from 'common/utils/utils'

export type FeatureExperimentFreeze = {
  isFrozen: boolean
  experiment: Experiment | null
  isLoading: boolean
}

export function useFeatureExperimentFreeze(
  featureId: number | undefined,
  environmentId: string,
): FeatureExperimentFreeze {
  const isExperimentEnabled = Utils.getFlagsmithHasFeature('experimental_flags')
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
